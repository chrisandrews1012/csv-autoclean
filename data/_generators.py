import random
from datetime import date

from faker import Faker

HR_COLUMNS = [
    "employee_id",
    "name",
    "age",
    "department",
    "gender",
    "hire_date",
    "salary",
    "email",
    "performance_rating",
]

ECOMMERCE_COLUMNS = [
    "order_id",
    "customer_name",
    "product_category",
    "quantity",
    "unit_price",
    "order_date",
    "shipping_country",
    "order_status",
]

MEDICAL_COLUMNS = [
    "patient_id",
    "age",
    "diagnosis",
    "blood_type",
    "admission_date",
    "treatment_cost",
    "insurance_provider",
    "follow_up_required",
]

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Support"]
GENDERS = ["Male", "Female"]
PRODUCT_CATEGORIES = ["Electronics", "Clothing", "Home", "Toys", "Books", "Sports"]
ORDER_STATUSES = ["Pending", "Shipped", "Delivered", "Cancelled", "Returned"]
COUNTRIES = ["US", "UK", "CA", "DE", "FR", "AU"]
BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
INSURANCE_PROVIDERS = ["Aetna", "BlueCross", "UnitedHealth", "Medicare", "Self-Pay"]
COMMON_DIAGNOSES = ["Hypertension", "Diabetes", "Asthma", "Migraine", "Arthritis"]
SENSITIVE_DIAGNOSES = ["Depression", "Anxiety Disorder", "Substance Use Disorder"]

Row = dict[str, object]


def build_hr_rows(n: int = 500, seed: int = 42) -> list[Row]:
    Faker.seed(seed)
    fake = Faker()
    rng = random.Random(seed)
    rows: list[Row] = []
    for i in range(n):
        hire_date = fake.date_between(start_date="-10y", end_date="today")
        rows.append(
            {
                "employee_id": i + 1,
                "name": fake.name(),
                "age": rng.randint(22, 65),
                "department": rng.choice(DEPARTMENTS),
                "gender": rng.choice(GENDERS),
                "hire_date": hire_date.isoformat(),
                "salary": round(rng.uniform(35_000, 150_000), 2),
                "email": fake.email(),
                "performance_rating": rng.randint(1, 5),
            }
        )
    return rows


def corrupt_hr_rows(rows: list[Row], seed: int = 42) -> list[Row]:
    rng = random.Random(seed)
    messy = [dict(row) for row in rows]

    for row in messy:
        if rng.random() < 0.3:
            salary = row["salary"]
            assert isinstance(salary, float)
            row["salary"] = f"${salary:,.0f}"

    for row in messy:
        if rng.random() < 0.2:
            parsed = date.fromisoformat(str(row["hire_date"]))
            row["hire_date"] = parsed.strftime("%m/%d/%Y")

    for row in messy:
        roll = rng.random()
        if roll < 0.15:
            row["department"] = str(row["department"]).lower()
        elif roll < 0.3:
            row["department"] = str(row["department"]).upper()
        if rng.random() < 0.15:
            row["gender"] = str(row["gender"]).lower()

    for row in messy:
        if rng.random() < 0.01:
            row["age"] = rng.choice([-5, 150, 200])

    for row in messy:
        if rng.random() < 0.05:
            row["salary"] = None
    for row in messy:
        if rng.random() < 0.08:
            row["email"] = None

    duplicate_count = max(1, len(messy) // 25)
    duplicates = [dict(row) for row in rng.sample(messy, duplicate_count)]
    messy.extend(duplicates)

    return messy


def build_ecommerce_rows(n: int = 400, seed: int = 42) -> list[Row]:
    Faker.seed(seed)
    fake = Faker()
    rng = random.Random(seed)
    rows: list[Row] = []
    for i in range(n):
        order_date = fake.date_between(start_date="-2y", end_date="today")
        rows.append(
            {
                "order_id": i + 1,
                "customer_name": fake.name(),
                "product_category": rng.choice(PRODUCT_CATEGORIES),
                "quantity": rng.randint(1, 10),
                "unit_price": round(rng.uniform(5, 500), 2),
                "order_date": order_date.isoformat(),
                "shipping_country": rng.choice(COUNTRIES),
                "order_status": rng.choice(ORDER_STATUSES),
            }
        )
    return rows


def corrupt_ecommerce_rows(rows: list[Row], seed: int = 42) -> list[Row]:
    rng = random.Random(seed)
    messy = [dict(row) for row in rows]

    for row in messy:
        if rng.random() < 0.3:
            price = row["unit_price"]
            assert isinstance(price, float)
            row["unit_price"] = f"${price:,.2f}"

    for row in messy:
        if rng.random() < 0.1:
            row["quantity"] = None

    for row in messy:
        if rng.random() < 0.15:
            row["shipping_country"] = str(row["shipping_country"]).lower()

    duplicate_count = max(1, len(messy) // 30)
    duplicates = [dict(row) for row in rng.sample(messy, duplicate_count)]
    messy.extend(duplicates)

    return messy


def build_medical_rows(n: int = 400, seed: int = 42) -> list[Row]:
    Faker.seed(seed)
    fake = Faker()
    rng = random.Random(seed)
    all_diagnoses = COMMON_DIAGNOSES + SENSITIVE_DIAGNOSES
    rows: list[Row] = []
    for i in range(n):
        admission_date = fake.date_between(start_date="-3y", end_date="today")
        rows.append(
            {
                "patient_id": i + 1,
                "age": rng.randint(1, 95),
                "diagnosis": rng.choice(all_diagnoses),
                "blood_type": rng.choice(BLOOD_TYPES),
                "admission_date": admission_date.isoformat(),
                "treatment_cost": round(rng.uniform(100, 20_000), 2),
                "insurance_provider": rng.choice(INSURANCE_PROVIDERS),
                "follow_up_required": rng.choice([True, False]),
            }
        )
    return rows


def corrupt_medical_rows(rows: list[Row], seed: int = 42) -> list[Row]:
    """Null out diagnosis more often when it's sensitive, an MNAR pattern.

    Missingness here depends on the value itself (a stigmatized diagnosis is
    less likely to be recorded), not on some other observed column. That's
    what makes it MNAR rather than MAR: no amount of looking at the other
    columns explains the missingness, only the (now-hidden) value would.
    """
    rng = random.Random(seed)
    messy = [dict(row) for row in rows]

    for row in messy:
        diagnosis = row["diagnosis"]
        drop_probability = 0.6 if diagnosis in SENSITIVE_DIAGNOSES else 0.03
        if rng.random() < drop_probability:
            row["diagnosis"] = None

    return messy
