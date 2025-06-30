# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 04:14:46 2025

@author: sachin
"""

import streamlit as st
import pandas as pd
import os
from openpyxl import load_workbook

# Load and process master stock data
df1 = pd.read_excel('MasterSheet1.xlsx')
df1.rename(columns={'Stock': 'Bannerghatta_Stock'}, inplace=True)

df2 = pd.read_excel('MasterSheet2.xlsx')
df2.rename(columns={'Stock': 'Mysore_Stock'}, inplace=True)

result = df1.merge(df2[['Design Name ', 'Mysore_Stock']], on='Design Name ', how='left')
result['TotalStock'] = result['Bannerghatta_Stock'] + result['Mysore_Stock']
result.sort_values(by='TotalStock', ascending=False, inplace=True)
results = result[['TotalStock','Design Name ','SubDesign', 'Supplier','Bannerghatta_Stock', 'Mysore_Stock']]

# Load and process sales data
sales1 = pd.read_excel('sales1.xlsx')
sales2 = pd.read_excel('sales2.xlsx')
Gb1 = sales1.groupby('Product')['Qty'].sum().reset_index()
Gb2 = sales2.groupby('Product')['Qty'].sum().reset_index()
Gb1.rename(columns={'Qty': 'Bannerghatta_Sale'}, inplace=True)
Gb2.rename(columns={'Qty': 'Mysore_Sale'}, inplace=True)
sales = Gb1.merge(Gb2[['Product', 'Mysore_Sale']], on='Product', how='left')
sales['TotalSales'] = sales['Bannerghatta_Sale'] + sales['Mysore_Sale']
sales.rename(columns={'Product': 'Design Name '}, inplace=True)
results = results.merge(sales, on='Design Name ', how='left')

results = results[['TotalSales','TotalStock','Design Name ', 'SubDesign', 'Supplier','Bannerghatta_Sale','Bannerghatta_Stock','Mysore_Sale','Mysore_Stock']]
results.sort_values(by='TotalSales', ascending=False, inplace=True)
results.fillna(0, inplace=True)
results = results.drop_duplicates(keep='first')
results.columns = results.columns.str.strip()

# Streamlit UI
st.title("Inventory Management Dashboard")

tabs = st.tabs([
    "Dashboard",
    "Critical Stock",
    "Branchwise Stock",
    "Sales Entry",
    "Purchase Entry",
    "Credit Note Entry",
    "Download Data"
])

# ---------------- Dashboard Tab ----------------
with tabs[0]:
    st.subheader("Overall Sales-Stock Data")

    # Sidebar Filters
    design_options = ['All'] + sorted(results['Design Name'].unique())
    subdesign_options = ['All'] + sorted(results['SubDesign'].unique())
    supplier_options = ['All'] + sorted(results['Supplier'].unique())

    Design_filter = st.sidebar.selectbox("Select Design", design_options)
    SubDesign_filter = st.sidebar.selectbox("Select SubDesign", subdesign_options)
    Supplier_filter = st.sidebar.selectbox("Select Supplier", supplier_options)

    score_min, score_max = st.sidebar.slider(
        "TotalStock Range",
        min_value=int(results['TotalStock'].min()),
        max_value=int(results['TotalStock'].max()),
        value=(int(results['TotalStock'].min()), int(results['TotalStock'].max()))
    )

    # Apply filters
    filtered_df = results.copy()
    if Design_filter != 'All':
        filtered_df = filtered_df[filtered_df['Design Name'] == Design_filter]
    if SubDesign_filter != 'All':
        filtered_df = filtered_df[filtered_df['SubDesign'] == SubDesign_filter]
    if Supplier_filter != 'All':
        filtered_df = filtered_df[filtered_df['Supplier'] == Supplier_filter]
    filtered_df = filtered_df[
        (filtered_df['TotalStock'] >= score_min) &
        (filtered_df['TotalStock'] <= score_max)
    ]

    st.dataframe(filtered_df)

# ---------------- Critical Stock Tab ----------------
with tabs[1]:
#    st.subheader("Critical Stock")
    st.subheader("🚨 Critical Stock Alert")

    # Load the summary Excel file
    summary_df = pd.read_excel("OverallSummary.xlsx")
    summary_df.columns = summary_df.columns.astype(str).str.strip()  # Clean column names

    # Define critical condition
    critical_condition = (
        (summary_df['TotalSales'] / 6 > summary_df['TotalStock']) |
        (summary_df['Bannerghatta_Sale'] / 6 > summary_df['Bannerghatta_Stock']) |
        (summary_df['Mysore_Sale'] / 6 > summary_df['Mysore_Stock'])
    )

    # Filter critical rows
    critical_df = summary_df[critical_condition].copy()

    # Highlight function
    def highlight_critical(row):
        if (
            row['TotalSales'] / 6 > row['TotalStock'] or
            row['Bannerghatta_Sale'] / 6 > row['Bannerghatta_Stock'] or
            row['Mysore_Sale'] / 6 > row['Mysore_Stock']
        ):
            return ['background-color: #ff9999'] * len(row)
        return [''] * len(row)

    st.markdown("### Showing Products with Potential Stock Shortage")

    st.dataframe(
        critical_df.style.apply(highlight_critical, axis=1),
        use_container_width=True
    )

# ---------------- Branchwise Stock Tab ----------------
with tabs[2]:
    st.subheader("🏢 Branchwise Stock Viewer")

    def load_and_filter(filepath):
        df = pd.read_excel(filepath)
        df.columns = df.columns.astype(str).str.strip()
        for col in ["Design Name", "SubDesign", "Supplier", "Branch"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return df

    df_master = load_and_filter("MasterSheet.xlsx")

    # Dropdown filter options
    design_options = ['All'] + sorted(df_master['Design Name'].dropna().unique())
    subdesign_options = ['All'] + sorted(df_master['SubDesign'].dropna().unique())
    supplier_options = ['All'] + sorted(df_master['Supplier'].dropna().unique())
    branch_options = ['All'] + sorted(df_master['Branch'].dropna().unique())

    # Filter controls
    Design_filter = st.selectbox("🎨 Select Design", design_options)
    SubDesign_filter = st.selectbox("🧩 Select SubDesign", subdesign_options)
    Supplier_filter = st.selectbox("🏭 Select Supplier", supplier_options)
    Branch_filter = st.selectbox("📍 Select Branch", branch_options)

    # Apply filters (branch filter included)
    filtered_df = df_master.copy()
    if Design_filter != 'All':
        filtered_df = filtered_df[filtered_df['Design Name'] == Design_filter]
    if SubDesign_filter != 'All':
        filtered_df = filtered_df[filtered_df['SubDesign'] == SubDesign_filter]
    if Supplier_filter != 'All':
        filtered_df = filtered_df[filtered_df['Supplier'] == Supplier_filter]
    if Branch_filter != 'All':
        filtered_df = filtered_df[filtered_df['Branch'] == Branch_filter]

    st.markdown("### 🗂️ Filtered Stock for Selected Branch")
    st.dataframe(
        filtered_df[['Design Name', 'SubDesign', 'Supplier', 'Branch', 'Stock']],
        use_container_width=True
    )

    # 🧠 Stock comparison across all branches (use original unfiltered df_master, without branch filter)
    comparison_df = df_master.copy()

    if Design_filter != 'All':
        comparison_df = comparison_df[comparison_df['Design Name'] == Design_filter]
    if SubDesign_filter != 'All':
        comparison_df = comparison_df[comparison_df['SubDesign'] == SubDesign_filter]
    if Supplier_filter != 'All':
        comparison_df = comparison_df[comparison_df['Supplier'] == Supplier_filter]

    st.markdown("### 📊 Stock Comparison Across Branches (All Branches)")

    if not comparison_df.empty:
        pivot_df = comparison_df.pivot_table(
            index=['Design Name', 'SubDesign', 'Supplier'],
            columns='Branch',
            values='Stock',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        st.dataframe(pivot_df, use_container_width=True)

        if len(pivot_df.columns.difference(['Design Name', 'SubDesign', 'Supplier'])) > 1:
            branch_totals = pivot_df.drop(columns=['Design Name', 'SubDesign', 'Supplier']).sum().to_frame().T
            st.bar_chart(branch_totals)



# ---------------- Sales Entry Tab ----------------
with tabs[3]:
    st.subheader("Sales Entry")

    # File path
    sales_file = "SalesMaster.xlsx"

    # Init session state for temp items
    if 'temp_sales_items' not in st.session_state:
        st.session_state['temp_sales_items'] = []

    with st.form("invoice_form"):
        st.write("### Invoice Details (Applies to all products below)")
        col1, col2 = st.columns(2)
        with col1:
            invoice_number = st.text_input("Invoice Number")
            invoice_date = st.date_input("Invoice Date")
            from_company = st.text_input("From")
            from_place = st.text_input("From_Place")
        with col2:
            buyer = st.text_input("Buyer")
            place = st.text_input("Place")

        st.write("### Product Line Item")
        col1, col2 = st.columns(2)
        with col1:
            product = st.text_input("Product")
            qty = st.number_input("Qty", min_value=0, step=1)
            unit = st.text_input("Unit", value="mtrs")
        with col2:
            rate = st.number_input("Rate", min_value=0.0, step=0.1)
            freight = st.number_input("Freight", min_value=0.0, step=0.1)
            gst_amt = st.number_input("GST Amount", min_value=0.0, step=0.1)
            gross_value = st.text_input("Gross Value (optional)", placeholder="Leave blank if same as Value")

        # Auto calculation
        value = qty * rate
        net_invoice = value + gst_amt + freight

        st.markdown(f"**Auto-calculated Value:** ₹{value:,.2f}")
        st.markdown(f"**Auto-calculated Net Invoice:** ₹{net_invoice:,.2f}")

        col_add, col_save = st.columns([1, 1])
        add_product = col_add.form_submit_button("➕ Add Product to List")
        save_invoice = col_save.form_submit_button("✅ Submit Full Invoice")

        if add_product:
            product_entry = {
                "Invoice number": invoice_number,
                "Invoice date": str(invoice_date),
                "From": from_company,
                "From_Place": from_place,
                "Buyer": buyer,
                "Place": place,
                "Product": product,
                "Qty": qty,
                "Unit": unit,
                "Rate": rate,
                "Value": value,
                "Gross value": gross_value if gross_value else value,
                "Freight": freight,
                "gst amt": gst_amt,
                "net invoice value": net_invoice
            }
            st.session_state['temp_sales_items'].append(product_entry)
            st.success("✅ Product added to invoice list!")

        if save_invoice and st.session_state['temp_sales_items']:
            try:
                new_data = pd.DataFrame(st.session_state['temp_sales_items'])

                if os.path.exists(sales_file):
                    existing_df = pd.read_excel(sales_file)
                    updated_df = pd.concat([existing_df, new_data], ignore_index=True)
                else:
                    updated_df = new_data

                updated_df.to_excel(sales_file, index=False)
                st.success("✅ Full Invoice saved successfully!")
                st.session_state['temp_sales_items'] = []  # Clear after saving
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Failed to save invoice: {e}")

    # Show current temp product list
    if st.session_state['temp_sales_items']:
        st.markdown("### 🧾 Current Products in Invoice")
        temp_df = pd.DataFrame(st.session_state['temp_sales_items'])
        st.dataframe(temp_df)

    # ---------------- Show Last 10 Entries ----------------
    st.markdown("---")
    st.subheader("📋 Last 10 Sales Entries")

    if os.path.exists(sales_file):
        df_sales = pd.read_excel(sales_file)
        df_recent = df_sales.tail(10).reset_index(drop=True)

        for idx, row in df_recent.iterrows():
            col1, col2 = st.columns([9, 1])
            with col1:
                st.write(row.to_dict())
            with col2:
                if st.button("❌ Delete", key=f"del_{idx}"):
                    full_index = df_sales.index[-10 + idx]
                    df_sales.drop(index=full_index, inplace=True)
                    df_sales.reset_index(drop=True, inplace=True)
                    df_sales.to_excel(sales_file, index=False)
                    st.success("✅ Entry deleted. Refreshing...")
                    st.experimental_rerun()
    else:
        st.info("No entries found yet.")

# ---------------- Purchase Entry Tab ----------------
with tabs[4]:
    st.subheader("Purchase Entry")

    purchase_file = "PurchaseMaster.xlsx"

    if "purchase_buffer" not in st.session_state:
        st.session_state.purchase_buffer = []

    with st.form("purchase_entry_form"):
        st.markdown("### Invoice Details")
        col1, col2 = st.columns(2)
        with col1:
            invoice_number = st.text_input("Invoice Number")
            invoice_date = st.date_input("Invoice Date")
            from_company = st.text_input("From")
            from_place = st.text_input("From_Place")
        with col2:
            buyer = st.text_input("Purchase (Buyer)")
            place = st.text_input("Place")

        st.markdown("### Product Entry")
        col3, col4 = st.columns(2)
        with col3:
            product = st.text_input("Product")
            qty = st.number_input("Qty", min_value=0, step=1)
            unit = st.text_input("Unit", value="mtrs")
        with col4:
            rate = st.number_input("Rate", min_value=0.0, step=0.1)
            freight = st.number_input("Freight", min_value=0.0, step=0.1)
            gst_amt = st.number_input("GST Amount", min_value=0.0, step=0.1)
            gross_value = st.text_input("Gross Value (optional)", placeholder="Leave blank if same as Value")

        value = qty * rate
        net_invoice = value + gst_amt + freight

        st.markdown(f"**Auto-calculated Value:** ₹{value:,.2f}")
        st.markdown(f"**Auto-calculated Net Invoice:** ₹{net_invoice:,.2f}")

        add_product = st.form_submit_button("➕ Add Product to Invoice")

        if add_product:
            entry = {
                "Invoice number": invoice_number,
                "Invoice date": str(invoice_date),
                "From": from_company,
                "From_Place": from_place,
                "Purchase": buyer,
                "Place": place,
                "Product": product,
                "Qty": qty,
                "Unit": unit,
                "Rate": rate,
                "Value": value,
                "Gross value": gross_value if gross_value else value,
                "Freight": freight,
                "gst amt": gst_amt,
                "net invoice value": net_invoice
            }
            st.session_state.purchase_buffer.append(entry)
            st.success("✅ Product added to invoice buffer.")

    if st.session_state.purchase_buffer:
        st.markdown("### Buffered Entries (Not Yet Saved):")
        st.table(pd.DataFrame(st.session_state.purchase_buffer))

        if st.button("💾 Save All to PurchaseMaster.xlsx"):
            try:
                df_new = pd.DataFrame(st.session_state.purchase_buffer)
                if os.path.exists(purchase_file):
                    df_existing = pd.read_excel(purchase_file)
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                else:
                    df_combined = df_new
                df_combined.index += 1
                df_combined.reset_index(inplace=True)
                df_combined.rename(columns={"index": "Sr. no"}, inplace=True)
                df_combined.to_excel(purchase_file, index=False)
                st.success("✅ All entries saved.")
                st.session_state.purchase_buffer.clear()
            except Exception as e:
                st.error(f"❌ Error saving to file: {e}")

    st.markdown("---")
    st.subheader("📋 Last 10 Purchase Entries")

    if os.path.exists(purchase_file):
        df_purchase = pd.read_excel(purchase_file)
        df_last10 = df_purchase.tail(10).reset_index(drop=True)

        for idx, row in df_last10.iterrows():
            col1, col2 = st.columns([9, 1])
            with col1:
                st.write(row.to_dict())
            with col2:
                if st.button("❌ Delete", key=f"del_purchase_{idx}"):
                    full_index = df_purchase.index[-10 + idx]
                    df_purchase.drop(index=full_index, inplace=True)
                    df_purchase.reset_index(drop=True, inplace=True)
                    df_purchase.index += 1
                    df_purchase.reset_index(inplace=True)
                    df_purchase.rename(columns={"index": "Sr. no"}, inplace=True)
                    df_purchase.to_excel(purchase_file, index=False)
                    st.success("✅ Entry deleted. Please refresh to see update.")
                    st.experimental_rerun()
    else:
        st.info("No purchase entries yet.")


# ---------------- Credit Note Entry Tab ----------------
with tabs[5]:
    st.subheader("Credit Note Entry")

    credit_file = "CreditNoteMaster.xlsx"

    if "credit_buffer" not in st.session_state:
        st.session_state.credit_buffer = []

    with st.form("credit_note_form"):
        st.markdown("### Invoice Details")
        col1, col2 = st.columns(2)
        with col1:
            invoice_number = st.text_input("Invoice Number")
            invoice_date = st.date_input("Invoice Date")
            from_company = st.text_input("From")
            from_place = st.text_input("From_Place")
        with col2:
            buyer = st.text_input("Buyer")
            place = st.text_input("Place")

        st.markdown("### Product Entry")
        col3, col4 = st.columns(2)
        with col3:
            product = st.text_input("Product")
            qty = st.number_input("Qty", min_value=0, step=1)
            unit = st.text_input("Unit", value="mtrs")
        with col4:
            rate = st.number_input("Rate", min_value=0.0, step=0.1)
            freight = st.number_input("Freight", min_value=0.0, step=0.1)
            gst_amt = st.number_input("GST Amount", min_value=0.0, step=0.1)
            gross_value = st.text_input("Gross Value (optional)", placeholder="Leave blank if same as Value")

        value = qty * rate
        net_invoice = value + gst_amt + freight

        st.markdown(f"**Auto-calculated Value:** ₹{value:,.2f}")
        st.markdown(f"**Auto-calculated Net Invoice:** ₹{net_invoice:,.2f}")

        add_product = st.form_submit_button("➕ Add Product to Credit Note")

        if add_product:
            entry = {
                "Invoice number": invoice_number,
                "Invoice date": str(invoice_date),
                "From": from_company,
                "From_Place": from_place,
                "Buyer": buyer,
                "Place": place,
                "Product": product,
                "Qty": qty,
                "Unit": unit,
                "Rate": rate,
                "Value": value,
                "Gross value": gross_value if gross_value else value,
                "Freight": freight,
                "gst amt": gst_amt,
                "net invoice value": net_invoice
            }
            st.session_state.credit_buffer.append(entry)
            st.success("✅ Product added to credit note buffer.")

    if st.session_state.credit_buffer:
        st.markdown("### Buffered Entries (Not Yet Saved):")
        st.table(pd.DataFrame(st.session_state.credit_buffer))

        if st.button("💾 Save All to CreditNoteMaster.xlsx"):
            try:
                df_new = pd.DataFrame(st.session_state.credit_buffer)
                if os.path.exists(credit_file):
                    df_existing = pd.read_excel(credit_file)
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                else:
                    df_combined = df_new
                df_combined.index += 1
                df_combined.reset_index(inplace=True)
                df_combined.rename(columns={"index": "Sr. no"}, inplace=True)
                df_combined.to_excel(credit_file, index=False)
                st.success("✅ All credit note entries saved.")
                st.session_state.credit_buffer.clear()
            except Exception as e:
                st.error(f"❌ Error saving to file: {e}")

    st.markdown("---")
    st.subheader("📋 Last 10 Credit Note Entries")

    if os.path.exists(credit_file):
        df_credit = pd.read_excel(credit_file)
        df_last10 = df_credit.tail(10).reset_index(drop=True)

        for idx, row in df_last10.iterrows():
            col1, col2 = st.columns([9, 1])
            with col1:
                st.write(row.to_dict())
            with col2:
                if st.button("❌ Delete", key=f"del_credit_{idx}"):
                    full_index = df_credit.index[-10 + idx]
                    df_credit.drop(index=full_index, inplace=True)
                    df_credit.reset_index(drop=True, inplace=True)
                    df_credit.index += 1
                    df_credit.reset_index(inplace=True)
                    df_credit.rename(columns={"index": "Sr. no"}, inplace=True)
                    df_credit.to_excel(credit_file, index=False)
                    st.success("✅ Entry deleted. Please refresh to see update.")
                    st.experimental_rerun()
    else:
        st.info("No credit note entries yet.")
        
        
with tabs[6]:
    st.subheader("📥 Download Data with Filters")

    def load_and_filter(file_path, label):
        if not os.path.exists(file_path):
            st.warning(f"{label} file not found.")
            return

        df = pd.read_excel(file_path)
        df.columns = df.columns.astype(str).str.strip()

        # Ensure correct date type
        if not pd.api.types.is_datetime64_any_dtype(df["Invoice date"]):
            df["Invoice date"] = pd.to_datetime(df["Invoice date"], errors="coerce")

        col1, col2, col3 = st.columns(3)
        with col1:
            invoice_number = st.selectbox(f"{label} - Invoice Number", options=["All"] + sorted(df["Invoice number"].dropna().unique().tolist()))
            buyer_column = "Buyer" if "Buyer" in df.columns else "Purchase"
            buyer = st.selectbox(f"{label} - {buyer_column}", options=["All"] + sorted(df[buyer_column].dropna().unique().tolist()))

        with col2:
            from_company = st.selectbox(f"{label} - From", options=["All"] + sorted(df["From"].dropna().unique().tolist()))
            product = st.selectbox(f"{label} - Product", options=["All"] + sorted(df["Product"].dropna().unique().tolist()))

        with col3:
            min_date = df["Invoice date"].min()
            max_date = df["Invoice date"].max()
            start_date = st.date_input(f"{label} - From Date", value=min_date, min_value=min_date, max_value=max_date)
            end_date = st.date_input(f"{label} - To Date", value=max_date, min_value=min_date, max_value=max_date)

        # --- Apply Filters ---
        filtered = df.copy()

        if invoice_number != "All":
            filtered = filtered[filtered["Invoice number"] == invoice_number]

        if buyer != "All":
            filtered = filtered[filtered[buyer_column] == buyer]

        if from_company != "All":
            filtered = filtered[filtered["From"] == from_company]

        if product != "All":
            filtered = filtered[filtered["Product"] == product]

        filtered = filtered[(filtered["Invoice date"] >= pd.to_datetime(start_date)) & (filtered["Invoice date"] <= pd.to_datetime(end_date))]

        # Show filtered table
        st.dataframe(filtered)

        # Download filtered data
        csv_data = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(f"⬇️ Download Filtered {label} Data", data=csv_data, file_name=f"{label}_Filtered.csv", mime="text/csv")

    st.markdown("### 🔽 Sales Data")
    load_and_filter("SalesMaster.xlsx", "Sales")

    st.markdown("---")
    st.markdown("### 🔽 Purchase Data")
    load_and_filter("PurchaseMaster.xlsx", "Purchase")

    st.markdown("---")
    st.markdown("### 🔽 Credit Note Data")
    load_and_filter("CreditNoteMaster.xlsx", "CreditNote")