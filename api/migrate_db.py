"""Script de migração para adicionar colunas faltantes no banco de dados."""
import sqlite3

def run_migration():
    conn = sqlite3.connect('vmaps.db')
    cursor = conn.cursor()

    # Adicionar coluna creator_color em places
    try:
        cursor.execute('ALTER TABLE places ADD COLUMN creator_color TEXT DEFAULT "blue"')
        print('✓ Adicionado creator_color em places')
    except Exception as e:
        print(f'× creator_color em places já existe ou erro: {e}')

    # Adicionar coluna is_public em maps
    try:
        cursor.execute('ALTER TABLE maps ADD COLUMN is_public INTEGER DEFAULT 0')
        print('✓ Adicionado is_public em maps')
    except Exception as e:
        print(f'× is_public em maps já existe ou erro: {e}')

    # Adicionar coluna marker_color em map_members
    try:
        cursor.execute('ALTER TABLE map_members ADD COLUMN marker_color TEXT DEFAULT "blue"')
        print('✓ Adicionado marker_color em map_members')
    except Exception as e:
        print(f'× marker_color em map_members já existe ou erro: {e}')

    conn.commit()
    conn.close()
    print('\n✓ Migração concluída!')

if __name__ == '__main__':
    run_migration()
