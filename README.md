# Inventory Digestion Exercise

## Summary

This project implements an end-to-end inventory data pipeline:

- A Python script extracts and transforms inventory data from an S3 source  
- A Ruby on Rails API stores the processed data in MongoDB using Mongoid  
- The API returns batch-level summaries such as average price and total quantity  

## How to Run

### 1. Start MongoDB

Make sure MongoDB is installed and running locally.

```bash
mongod --dbpath C:\data\db
```

### 2. Start the API

Navigate to the Rails project folder:

```bash
cd inventory_api
```

Start the Rails server:

```bash
ruby bin/rails server
```

The API will be available at:  
http://localhost:3000

### 3. Run the Python Script

Navigate to the Python folder:

```bash
cd inventory_exercise
```

Generate CSV:

```bash
python integration-exercise.py generate_csv
```

Upload data to the API:

```bash
python integration-exercise.py upload
```

List uploaded batches:

```bash
python integration-exercise.py list_uploads
```

## Notes

- MongoDB must be running before starting the API  
- The API must be running before uploading or listing data  
