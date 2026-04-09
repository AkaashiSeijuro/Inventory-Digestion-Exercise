# Inventory Digestion Exercise

This project processes inventory data and stores it through an API.

It has two main parts:

- **inventory_api:** Ruby on Rails API (stores and aggregates data using MongoDB)
- **inventory_exercise:** Python script (extracts, transforms, and sends data)

---

## Overview of Workflow

1. The Python script downloads inventory data from an S3 source
2. The data is cleaned and transformed
3. The transformed data can:
   - be saved as a CSV file
   - be sent to the API
4. The API stores the data in MongoDB
5. The API can return summary statistics for each upload batch

---

## Setup Instructions

### 1. Start MongoDB

Make sure MongoDB is running locally before starting the API.

---

### 2. Start the API

Navigate into the `inventory_api` folder and start the Rails server.

Once running, the API will be available at:

http://localhost:3000

---

### 3. Run the Python Script

Navigate into the `inventory_exercise` folder.

The script supports three actions:

#### Generate CSV
Processes the raw data and creates a CSV file with the transformed results.

#### Upload Data
Sends the processed data to the API, which stores it in MongoDB.

#### List Uploads
Retrieves batch summaries from the API, including:
- number of records
- average price
- total quantity

---

## API Endpoints

### POST /inventory_uploads.json

Accepts a JSON array of inventory records and stores them as a batch.

Returns:
- batch_id
- number_of_units

---

### GET /inventory_uploads.json

Returns a list of uploaded batches with:
- batch_id
- number_of_units
- average_price
- total_quantity

---

## Key Implementation Details

### Python
- Uses only built-in libraries (no pandas or numpy)
- Parses CSV data using `csv.DictReader`
- Applies pricing rules based on margin
- Validates UPC values
- Generates tags and structured properties

### Rails API
- Uses MongoDB with Mongoid (no ActiveRecord)
- Stores each upload as a batch
- Uses aggregation to compute batch statistics efficiently

---

## Notes

- MongoDB must be running before using the API
- The API must be running before using the upload or listing features
- The Python script handles both file generation and API interaction
