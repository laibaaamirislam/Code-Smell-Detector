# Code-Smell-Detector

A web-based Java code smell detection tool built for Feature Envy and Data Clumps.

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Run the app

```bash
streamlit run streamlit_app.py
```

## 3) Use the detector

1. Enter a Java source folder path (default: `sample_java_files`).
   - For safety, the app only scans folders inside this project directory.
2. Click **Run Detection**.
3. Review findings in the dashboard table with highlighted smell badges.

## Detection Rules

- **Feature Envy**: A method is flagged when it has at least 3 external interactions and those exceed interactions with its own class members.
- **Data Clumps**: Flagged when 3 or more identical fields (`type + name`) are shared across classes.

## Included sample files

Use `sample_java_files/` for quick testing:

- `Customer.java`
- `Employee.java`
- `OrderService.java`
