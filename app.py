import streamlit as st
from web3 import Web3

st.set_page_config(page_title="HalalChain Lab", page_icon="📜")
st.title("📜 HalalChain Lab")
st.write("Sistem Sertifikasi Halal berbasis Blockchain ERC-721")

st.subheader("1. Status Blockchain Lokal")
# Hubungkan ke Node Lokal Hardhat
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

if w3.is_connected():
    st.success("Terhubung ke Blockchain Lokal (Hardhat)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Chain ID", value=w3.eth.chain_id)
    with col2:
        st.metric(label="Block Terbaru", value=w3.eth.block_number)
else:
    st.error("Gagal terhubung ke Node Lokal. Pastikan 'npx hardhat node' berjalan.")

st.subheader("2. Informasi Wallet & Contract")
contract_address = st.text_input("Alamat Contract HalalChain:", "0x5FbDB2315678afecb367f032d93F642f64180aa3")
user_address = st.text_input("Alamat Akun Pengguna (MetaMask/Hardhat):")

if user_address:
    try:
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(user_address))
        balance_eth = w3.from_wei(balance_wei, 'ether')
        st.info(f"Saldo Akun: **{balance_eth} ETH**")
    except Exception as e:
        st.error(f"Alamat wallet tidak valid: {e}")