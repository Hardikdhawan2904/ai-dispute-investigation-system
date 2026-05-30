"""
Seed 1000 bank customers (CUST-00001 to CUST-01000) with basic info only.

Run from the backend directory:
    python scripts/seed_customers.py
"""
import sys, os, random, string
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(Path(__file__).parent.parent)

from dotenv import load_dotenv
load_dotenv()

from database.database import SessionLocal, init_db
from database.models import BankCustomer

FIRST_NAMES = [
    "Aarav","Aditya","Akash","Amit","Ananya","Anjali","Ankit","Ansh",
    "Arjun","Aryan","Ayaan","Ayesha","Bhavna","Chetan","Deepa","Deepak",
    "Dhruv","Divya","Farhan","Gauri","Hardik","Harsh","Isha","Ishaan",
    "Jaya","Kabir","Karan","Kavya","Khushi","Krishna","Kunal","Lakshmi",
    "Manish","Meera","Mihir","Mohan","Mohit","Nandini","Neha","Nikhil",
    "Nikita","Nisha","Palak","Parth","Pooja","Prachi","Pranav","Priya",
    "Rahul","Raj","Rajesh","Ramesh","Ravi","Riya","Rohit","Rohan",
    "Sachin","Sahil","Sanaya","Sanjay","Sara","Shruti","Shubham","Simran",
    "Sneha","Sonal","Suresh","Swati","Tanvi","Tarun","Uday","Varun",
    "Vidya","Vikram","Virat","Vishal","Yash","Zara","Zoya","Abhishek",
    "Aditi","Alok","Amrita","Ankita","Apoorv","Archana","Ashish","Astha",
    "Bhuvan","Chirag","Disha","Esha","Gaurav","Hemant","Ishan","Jatin",
    "Kiran","Komal","Lalit","Madhav","Megha","Namrata","Naveen","Neeraj",
]

LAST_NAMES = [
    "Agarwal","Arora","Bahl","Bajaj","Batra","Bhatt","Chauhan","Chopra",
    "Choudhari","Das","Dave","Desai","Deshpande","Dutta","Gandhi","Garg",
    "Ghosh","Goyal","Gupta","Iyer","Jain","Jha","Joshi","Kapur",
    "Kapoor","Kaur","Khan","Khanna","Kumar","Lal","Malhotra","Mehta",
    "Menon","Mishra","Mittal","Modi","Nair","Pandey","Patel","Pathak",
    "Pillai","Rao","Rastogi","Reddy","Saha","Saxena","Shah","Sharma",
    "Shukla","Singh","Sinha","Srivastava","Tiwari","Trivedi","Varma",
    "Verma","Yadav","Bose","Chandra","Roy","Banerjee","Chatterjee",
    "Mukherjee","Bhat","Hegde","Kulkarni","Patil","Naik","Sawant",
]

EMAIL_DOMAINS = ["gmail.com","yahoo.com","outlook.com","hotmail.com","rediffmail.com"]

def _phone():
    return random.choice(["6","7","8","9"]) + "".join(random.choices(string.digits, k=9))

def seed():
    init_db()
    db = SessionLocal()

    # Clear existing customers
    db.query(BankCustomer).delete()
    db.commit()

    print("Seeding 1000 bank customers…")

    used_emails = set()
    for i in range(1, 1001):
        customer_id = f"CUST-{i:05d}"
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        name  = f"{first} {last}"

        # ensure unique email
        base_email = f"{first.lower()}.{last.lower()}"
        email = f"{base_email}@{random.choice(EMAIL_DOMAINS)}"
        if email in used_emails:
            email = f"{base_email}{i}@{random.choice(EMAIL_DOMAINS)}"
        used_emails.add(email)

        db.add(BankCustomer(
            customer_id = customer_id,
            full_name   = name,
            email       = email,
            phone       = _phone(),
        ))

        if i % 200 == 0:
            db.commit()
            print(f"  {i}/1000 inserted…")

    db.commit()
    db.close()
    print("Done — 1000 customers seeded.")

if __name__ == "__main__":
    seed()
