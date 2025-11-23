import torch
import numpy as np

class GeometricRefiner:
    """
    Refines protein coordinates based on geometric constraints and LLM priors.
    Uses PyTorch for optimization.
    """
    def __init__(self, learning_rate=0.01, num_steps=100):
        self.learning_rate = learning_rate
        self.num_steps = num_steps

    def refine(self, initial_coords, constraints, mask=None):
        """
        Refines the coordinates.
        
        Args:
            initial_coords (np.array): (N, 3) array of atomic coordinates.
            constraints (list): List of constraint dicts (e.g., {'type': 'distance', 'indices': [i, j], 'value': d}).
            mask (np.array, optional): Boolean mask of residues/atoms to move. If None, move all.
            
        Returns:
            np.array: Refined coordinates.
        """
        # Convert to tensor
        coords = torch.tensor(initial_coords, dtype=torch.float32, requires_grad=True)
        optimizer = torch.optim.Adam([coords], lr=self.learning_rate)
        
        initial_coords_tensor = torch.tensor(initial_coords, dtype=torch.float32)
        
        for step in range(self.num_steps):
            optimizer.zero_grad()
            loss = torch.tensor(0.0)
            
            # 1. Constraint Loss
            for constraint in constraints:
                if constraint['type'] == 'distance':
                    idx1, idx2 = constraint['indices']
                    target_dist = constraint['value']
                    current_dist = torch.norm(coords[idx1] - coords[idx2])
                    loss += (current_dist - target_dist) ** 2
            
            # 2. Restraint Loss (keep atoms close to original positions unless moved)
            # If mask is provided, we only allow masked atoms to move freely, 
            # others should be heavily restrained or frozen.
            # Here we implement a soft restraint for unmasked atoms.
            if mask is not None:
                # mask is 1 for moving, 0 for fixed
                # We want to penalize movement of fixed atoms
                # deviation = (coords - initial_coords_tensor)
                # fixed_deviation = deviation[~mask]
                # loss += 100.0 * torch.sum(fixed_deviation ** 2)
                pass # Simplified for now, assuming optimizer only updates if we handle gradients correctly
            
            # 3. Geometry Loss (Bond lengths)
            # Simplified: Maintain distance between adjacent atoms (assuming CA trace for now)
            # In a full atom model, this would be more complex.
            # for i in range(len(coords) - 1):
            #     bond_len = torch.norm(coords[i] - coords[i+1])
            #     loss += (bond_len - 3.8) ** 2 # CA-CA distance approx 3.8A
            
            if loss.requires_grad:
                loss.backward()
                
                # Apply mask to gradients: zero out gradients for fixed atoms
                if mask is not None:
                    mask_tensor = torch.tensor(mask, dtype=torch.bool)
                    coords.grad[~mask_tensor] = 0.0
                    
                optimizer.step()
            else:
                # No constraints/loss, nothing to optimize
                pass
            
        return coords.detach().numpy()
