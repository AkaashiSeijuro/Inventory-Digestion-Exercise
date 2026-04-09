# Inventory Digestion Exercise

## Structure

- inventory_api - Rails API (MongoDB + Mongoid)
- inventory_exercise - Python ETL script

## Run

### Start MongoDB

### Start Rails
cd inventory_api  
ruby bin/rails server  

### Run Python
cd inventory_exercise  
python integration-exercise.py generate_csv  
python integration-exercise.py upload  
python integration-exercise.py list_uploads  
