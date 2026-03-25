# Setup once
conda env create -f environment.yml
conda activate surveillance

# Daily use
conda activate surveillance
python3 main.py
```

**Why conda is better for this project:**
```
pip install opencv + numpy   → version conflicts (you hit this!)
conda install opencv + numpy → conda resolves all binaries together
