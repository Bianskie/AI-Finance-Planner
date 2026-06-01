import json
import os

# Nama File Database
DB_FILE = 'database.json'

def get_all_transactions():
    """Function to read all contents of the JSON database"""
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        return []
        
    with open(DB_FILE, 'r') as file:
        return json.load(file)

def save_transactions(data):
    """Function to rewrite data into the JSON file"""
    with open(DB_FILE, 'w') as file:
        json.dump(data, file, indent=4) 

def add_transaction(category, trans_type, amount, date):
    """Function to insert a new transaction"""
    transactions = get_all_transactions()
    
    new_id = 1 if len(transactions) == 0 else transactions[-1]['id'] + 1
    
    new_record = {
        "id": new_id,
        "category": category,
        "type": trans_type,
        "amount": amount,
        "date": date
    }
    
    transactions.append(new_record)
    save_transactions(transactions)
    print(f"✅ Successfully saved: {trans_type} - {category} of Rp{amount}")

def delete_transaction(trx_id):
    """Function to delete a transaction by its ID"""
    transactions = get_all_transactions()
    # Simpan semua data KECUALI data yang ID-nya mau dihapus
    updated_transactions = [t for t in transactions if t['id'] != trx_id]
    save_transactions(updated_transactions)
    print(f"✅ Successfully deleted transaction ID: {trx_id}")
    