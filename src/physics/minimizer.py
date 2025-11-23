import sys
try:
    import openmm as mm
    import openmm.app as app
    import openmm.unit as unit
    OPENMM_AVAILABLE = True
except ImportError:
    try:
        import simtk.openmm as mm
        import simtk.openmm.app as app
        import simtk.unit as unit
        OPENMM_AVAILABLE = True
    except ImportError:
        OPENMM_AVAILABLE = False

class EnergyMinimizer:
    """
    Performs energy minimization using OpenMM.
    """
    def __init__(self, forcefield='amber14-all.xml', water_model='amber14/tip3p.xml'):
        self.forcefield_name = forcefield
        self.water_model = water_model

    def minimize(self, pdb_path, output_path):
        """
        Minimizes the structure in the PDB file.
        
        Args:
            pdb_path (str): Path to input PDB.
            output_path (str): Path to save minimized PDB.
        """
        if not OPENMM_AVAILABLE:
            print("Warning: OpenMM not found. Skipping minimization.")
            # Just copy the file or do nothing
            # For now, we'll just read and write it back to ensure flow works
            with open(pdb_path, 'r') as f:
                content = f.read()
            with open(output_path, 'w') as f:
                f.write(content)
            return

        try:
            pdb = app.PDBFile(pdb_path)
            forcefield = app.ForceField(self.forcefield_name, self.water_model)
            
            # Create system
            # We use a simple vacuum or implicit solvent model for efficiency if explicit water isn't needed
            # For refinement, implicit solvent (GB/SA) is often better/faster than setting up a box
            system = forcefield.createSystem(pdb.topology, nonbondedMethod=app.NoCutoff, constraints=app.HBonds)
            
            integrator = mm.LangevinIntegrator(300*unit.kelvin, 1.0/unit.picosecond, 2.0*unit.femtoseconds)
            simulation = app.Simulation(pdb.topology, system, integrator)
            simulation.context.setPositions(pdb.positions)
            
            print("Minimizing energy...")
            simulation.minimizeEnergy()
            
            positions = simulation.context.getState(getPositions=True).getPositions()
            
            print(f"Saving minimized structure to {output_path}")
            with open(output_path, 'w') as f:
                app.PDBFile.writeFile(pdb.topology, positions, f)
                
        except Exception as e:
            print(f"Error during minimization: {e}")
            # Fallback: copy input to output
            with open(pdb_path, 'r') as f:
                content = f.read()
            with open(output_path, 'w') as f:
                f.write(content)
