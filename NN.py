import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import gym
from gym import spaces
import numpy as np
from typing import List, Tuple, Dict
class EVDecisionNetwork(nn.Module):
    def __init__(self):
        super(EVDecisionNetwork, self).__init__()
        self.fc1 = nn.Linear(2, 64)  # 2 input features: remaining range and nearest station range
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 2)  # 2 output classes: 0 = don't branch, 1 = branch


    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)  # Output raw scores for each class
        return x
    
    

def train(training_data):
    # Extract inputs and labels
    inputs = torch.tensor([data[0] for data in training_data]).float()  # Convert to float for NN processing
    labels = torch.tensor([data[1] for data in training_data]).long()  # Convert to long because these are categorical labels

    # Create a TensorDataset and DataLoader
    train_dataset = TensorDataset(inputs, labels)
    train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True)

    # Step 2: Define the Network, Loss Function, and Optimizer
    model = EVDecisionNetwork()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Step 3: Training Loop
    num_epochs = 100  # Number of epochs to train for

    for epoch in range(num_epochs):
        for inputs, labels in train_loader:
            # Zero the parameter gradients
            optimizer.zero_grad()
        
            # Forward pass
            outputs = model(inputs)
        
            # Compute loss
            loss = criterion(outputs, labels)
        
            # Backward pass and optimize
            loss.backward()
            optimizer.step()
    
        # Optionally print the loss every x epochs
        if epoch % 1 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

    print("Training complete.")
        