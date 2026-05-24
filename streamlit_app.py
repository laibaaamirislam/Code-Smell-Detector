from pathlib import Path

import pandas as pd
import streamlit as st

from detector import detect_code_smells


st.set_page_config(page_title="Code Smell Detector", layout="wide")

st.markdown(
    """
    <style>
    .metric-card {background: #0f172a; border-radius: 12px; padding: 12px; color: #f8fafc;}
    .badge-feature {background-color: #dc2626; color: white; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600;}
    .badge-clumps {background-color: #d97706; color: white; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600;}
    .badge-other {background-color: #334155; color: white; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600;}
    table {width: 100%; border-collapse: collapse;}
    th, td {border-bottom: 1px solid #e2e8f0; padding: 12px; text-align: left;}
    th {background-color: #f8fafc;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Java Code Smell Detector")
st.caption("Detects Feature Envy and Data Clumps from Java source code using javalang AST parsing.")

project_root = Path(__file__).resolve().parent
default_folder = str(project_root / "sample_java_files")
folder_path = st.text_input("Java source folder path", value=default_folder)


def resolve_scan_directory(input_path: str) -> Path:
    raw_path = Path(input_path).expanduser()
    candidate = raw_path.resolve() if raw_path.is_absolute() else (project_root / raw_path).resolve()
    if not str(candidate).startswith(str(project_root)):
        raise ValueError("Path must stay inside the project directory.")
    return candidate


if st.button("Run Detection", type="primary"):
    try:
        target_path = resolve_scan_directory(folder_path)
    except ValueError as exc:
        st.error(str(exc))
    else:
        if not target_path.exists() or not target_path.is_dir():
            st.error("Please provide a valid folder path.")
        else:
            with st.spinner("Analyzing Java files..."):
                rows = detect_code_smells(target_path)

            total = len(rows)
            feature_envy = sum(1 for row in rows if row["Code Smell Type"] == "Feature Envy")
            data_clumps = sum(1 for row in rows if row["Code Smell Type"] == "Data Clumps")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Findings", total)
            col2.metric("Feature Envy", feature_envy)
            col3.metric("Data Clumps", data_clumps)

            if not rows:
                st.success("No smells were detected in the selected folder.")
            else:
                st.subheader("Detection Results")

            def indicator(smell: str) -> str:
                if smell == "Feature Envy":
                    return "🔴 High"
                if smell == "Data Clumps":
                    return "🟠 Medium"
                return "⚪ Info"

                result_df = pd.DataFrame(rows)
                result_df.insert(3, "Indicator", result_df["Code Smell Type"].map(indicator))

            def style_rows(row):
                if row["Code Smell Type"] == "Feature Envy":
                    style = "background-color: #fee2e2; color: #991b1b; font-weight: 600;"
                elif row["Code Smell Type"] == "Data Clumps":
                    style = "background-color: #ffedd5; color: #9a3412; font-weight: 600;"
                else:
                    style = ""
                return ["", "", style, style, ""]

                styled = result_df.style.apply(style_rows, axis=1)
                st.dataframe(styled, use_container_width=True, hide_index=True)
