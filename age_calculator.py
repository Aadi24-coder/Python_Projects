from datetime import date

birth_year = int(input("Enter birth year: "))
birth_month = int(input("Enter birth month (1-12): "))
birth_day = int(input("Enter birth day: "))

today = date.today()
birth_date = date(birth_year, birth_month, birth_day)

age = today.year - birth_date.year - ((today.month, today.day) < (birth_month, birth_day))

print(f"Your current age is: {age} years")