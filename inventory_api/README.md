# Inventory Digestion Exercise

This project consists of two parts:

- **inventory_api**: A Ruby on Rails API that stores and summarizes inventory data using MongoDB (Mongoid).
- **inventory_exercise**: A Python script that extracts, transforms, and uploads inventory data.

---

## How the system works

1. The Python script downloads raw inventory data from an S3 source.
2. It transforms the data according to business rules (pricing, tags, formatting).
3. The transformed data can:
   - be saved as a CSV file
   - be uploaded to the Rails API
4. The Rails API stores the data and provides summary statistics per upload batch.

---

## Setup Instructions

### 1. Start MongoDB

The Rails API uses MongoDB as its database.  
Make sure MongoDB is installed and running locally before starting the API.

---

### 2. Start the Rails API

Navigate into the `inventory_api` folder and start the server.

This will launch the API at:
