"""
Script para adicionar a coluna 'color' na tabela map_members
"""
import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'vmaps.db')

try:
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(map_members)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'color' in columns:
        print("✓ Coluna 'color' já existe na tabela map_members")
    else:
        # Adicionar a coluna
        print("Adicionando coluna 'color' na tabela map_members...")
        cursor.execute("""
            ALTER TABLE map_members 
            ADD COLUMN color VARCHAR(7) DEFAULT '#3B82F6'
        """)
        conn.commit()
        print("✓ Coluna 'color' adicionada com sucesso!")
    
    conn.close()
    print("\n✓ Banco de dados atualizado!")
    
except sqlite3.Error as e:
    print(f"✗ Erro ao atualizar banco de dados: {e}")
except Exception as e:
    print(f"✗ Erro inesperado: {e}")
