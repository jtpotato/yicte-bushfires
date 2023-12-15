import numpy as np
import torch
import torch.nn as nn

from training.Visualise import generate_visualisation

device=torch.device("cpu")

# if torch.backends.mps.is_available() and torch.backends.mps.is_built():
#     print("Using MPS.")
#     device = torch.device("mps")

loss_function = torch.compile(nn.MSELoss(), fullgraph=True, mode="max-autotune")

def train_loop(X_train, X_test, y_train, y_test, train_loader, firetrace_model, saved_epochs, additional_epochs, width, depth):
    firetrace_model.to(device)

    optimizer = torch.optim.Adam(firetrace_model.parameters(), lr=1e-5)

    best_loss = np.inf
    mega_epochs_since_best = 0

    for epoch in range(saved_epochs, saved_epochs + additional_epochs):
        epoch_loss = 0.0
        # Iterate over the DataLoader for training data
        for i, data in enumerate(train_loader, 0):
            # Get and prepare inputs
            inputs, targets = data
            inputs, targets = inputs.float().to(device), targets.float().to(device)
            targets = targets.reshape((targets.shape[0], 1))

            # Zero the gradients
            optimizer.zero_grad()

            outputs = firetrace_model(inputs)

            loss = loss_function(outputs, targets)

            # Perform backward pass
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        if epoch % 100 == 0:
            # Validate model
            test_output = firetrace_model(torch.tensor(X_test).float().to(device))
            test_loss = loss_function(test_output, torch.tensor(y_test, dtype=torch.float32, device=device).float()).item()

            print(
                f"Epoch {epoch} | Loss: {epoch_loss / len(train_loader)} | Val Loss: {test_loss} | Sample Output: {test_output[50].item()} | Actual: {y_test[50]}"
            )

            generate_visualisation(firetrace_model, epoch)

            if test_loss < best_loss:
                best_loss = test_loss
                mega_epochs_since_best = 0
                torch.save(
                    {
                        "model_state_dict": firetrace_model.state_dict(),
                        "epochs": epoch,
                        "model_size": [width, depth],
                    },
                    "models/firetrace_model.pt",
                )
                print(f"SAVED MODEL AT EPOCH {epoch}")
            else:
                mega_epochs_since_best += 1

            if mega_epochs_since_best > 20:
                print("EARLY STOPPING")
                break
