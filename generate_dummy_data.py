import json
import numpy as np
from Bio.PDB import Structure, Model, Chain, Residue, Atom
from Bio.PDB import PDBIO

def create_dummy_pdb(filename="test.pdb"):
    # Create a simple structure: 20 residues
    # Just a straight line of CA atoms for simplicity
    s = Structure.Structure("test")
    m = Model.Model(0)
    c = Chain.Chain("A")
    s.add(m)
    m.add(c)
    
    for i in range(20):
        res = Residue.Residue(("ALA", i+1, " "), "ALA", i+1)
        # Coordinates: straight line along X
        x = i * 3.8
        y = 0.0
        z = 0.0
        atom = Atom.Atom("CA", [x, y, z], 1.0, 1.0, " ", "CA", i+1, "C")
        res.add(atom)
        c.add(res)
        
    io = PDBIO()
    io.set_structure(s)
    io.save(filename)
    print(f"Created {filename}")

def create_dummy_json(filename="test.json"):
    # 20 residues
    # Residues 5-10 have low confidence (< 70)
    plddt = [90.0] * 20
    for i in range(5, 10):
        plddt[i] = 50.0
        
    data = {"plddt": plddt}
    with open(filename, 'w') as f:
        json.dump(data, f)
    print(f"Created {filename}")

if __name__ == "__main__":
    create_dummy_pdb()
    create_dummy_json()
