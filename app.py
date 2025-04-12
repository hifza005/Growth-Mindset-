from curses.ascii import alt
import streamlit as st
import pandas as pd
import os
from io import BytesIO
from zipfile import ZipFile

# Set up Streamlit app
st.set_page_config(page_title="Data Sweeper", layout='wide')
st.title("Data Sweeper")
st.write("Transform and analyze your files with built-in cleaning, visualization, and filtering.")

# File uploader
uploaded_files = st.file_uploader("Upload your files (CSV or Excel):", type=["csv", "xlsx"], accept_multiple_files=True)

processed_files = {}

if uploaded_files:
    for file in uploaded_files:
        file_ext = os.path.splitext(file.name)[-1].lower()
        
        if file_ext == ".csv":
            df = pd.read_csv(file)
        elif file_ext == ".xlsx":
            df = pd.read_excel(file)
        else:
            st.error(f"Unsupported file type: {file_ext}")
            continue
        
        # Display file info
        st.write(f"**File Name:** {file.name}")
        st.write(f"**File Size:** {file.size / 1024:.2f} KB")
        
        # Show first 5 rows
        st.write("**Preview of the Dataframe**")
        st.dataframe(df.head())
        
        # Summary Statistics
        st.subheader("📊 Summary Statistics")
        st.write(df.describe())
        
        # Data Cleaning Options
        st.subheader("🧹 Data Cleaning Options")
        if st.checkbox(f"Clean Data for {file.name}"):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"Remove Duplicates from {file.name}"):
                    df.drop_duplicates(inplace=True)
                    st.write("✅ Duplicates Removed!")
            
            with col2:
                if st.button(f"Fill Missing Values for {file.name}"):
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                    st.write("✅ Missing values filled!")
        
        # Data Filtering
        st.subheader("🔍 Data Filtering")
        selected_column = st.selectbox(f"Select a column to filter in {file.name}", df.columns)
        unique_values = df[selected_column].unique()
        filter_value = st.selectbox(f"Choose value to filter {selected_column}", unique_values)
        df = df[df[selected_column] == filter_value]
        
        # Column Selection
        st.subheader("🛠 Select Columns to Keep")
        columns = st.multiselect(f"Choose columns for {file.name}", df.columns, default=df.columns)
        df = df[columns]
        
        # Data Visualization Section
        st.subheader(f"📊 Data Visualization for {file.name}")
        if st.checkbox(f"Show visualization for {file.name}"):
            numeric_cols = df.select_dtypes(include='number').columns
            if not numeric_cols.empty:
                selected_col = st.selectbox(f"Select a column for visualization ({file.name})", numeric_cols, key=f"col_{file.name}")
                
                # Ensure chart_type is always defined
                chart_type = st.radio("Choose Chart Type", ["Bar Chart", "Line Chart", "Histogram", "Scatter Plot", "Pie Chart"], key=f"chart_{file.name}")

                if chart_type == "Bar Chart":
                    st.bar_chart(df[selected_col])

                elif chart_type == "Line Chart":
                    st.line_chart(df[selected_col])

                elif chart_type == "Histogram":
                    fig, ax = alt.subplots()
                    ax.hist(df[selected_col], bins=20, edgecolor="black")
                    st.pyplot(fig)

                elif chart_type == "Scatter Plot":
                    selected_col2 = st.selectbox("Select another column for Scatter Plot", numeric_cols, key=f"scatter_{file.name}")
                    fig, ax = alt.subplots()
                    ax.scatter(df[selected_col], df[selected_col2])
                    ax.set_xlabel(selected_col)
                    ax.set_ylabel(selected_col2)
                    st.pyplot(fig)

                elif chart_type == "Pie Chart":
                    fig, ax = alt.subplots()
                    df[selected_col].value_counts().plot.pie(autopct="%1.1f%%", ax=ax)
                    st.pyplot(fig)

            else:
                st.warning("No numeric columns available for visualization.")
        
        # File Conversion
        st.subheader(f"🔄 File Conversion Options for {file.name}")
        conversion_type = st.radio(f"Convert {file.name} to:", ["CSV", "Excel"], key=f"convert_{file.name}")

        buffer = BytesIO()
        if conversion_type == "CSV":
            df.to_csv(buffer, index=False)
            file_name = file.name.replace(file_ext, ".csv")
            mime_type = "text/csv"
        elif conversion_type == "Excel":
            df.to_excel(buffer, index=False, engine="openpyxl")
            file_name = file.name.replace(file_ext, ".xlsx")
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        buffer.seek(0)
        processed_files[file_name] = (buffer, mime_type)
        
        st.download_button(
            label=f"Download {file.name} as {conversion_type}",
            data=buffer,
            file_name=file_name,
            mime=mime_type
        )

    # Convert all files at once
    if processed_files and st.button("Download All Processed Files as ZIP"):
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zip_file:
            for name, (file_buffer, _) in processed_files.items():
                zip_file.writestr(name, file_buffer.getvalue())
        zip_buffer.seek(0)
        st.download_button("Download ZIP", data=zip_buffer, file_name="processed_files.zip", mime="application/zip")

st.success("All files processed ✅")
