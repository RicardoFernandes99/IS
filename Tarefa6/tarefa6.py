import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time
import os


LISTA_INSTITUICOES_URL = "https://www.dges.gov.pt/coloc/2025/col1listas.asp"
LISTA_CURSOS_URL = "https://www.dges.gov.pt/coloc/2025/col1listaredir.asp"
LISTA_COL_URL = "https://www.dges.gov.pt/coloc/2025/col1listacol.asp"

# Simular Browser 
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
})

TIPOS_INSTITUICAO = [
    {"Tipo": "Universidade", "CodR": "11"},
    {"Tipo": "Politécnico", "CodR": "12"}
]

DELAY = 0.1  

def get_instituicoes(codR):
    url = f"{LISTA_INSTITUICOES_URL}?CodR={codR}&action=2"
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    insts = []
    for opt in soup.find_all("option"):
        val = opt.get("value")
        if val and val.strip().isdigit():  
            full_text = opt.text.strip()
            
            current_code = val.strip()
            
            import re
            pattern = rf"{current_code} - ([^0-9]+?)(?=\d{{4}} - |\s*$)"
            match = re.search(pattern, full_text)
            
            if match:
                institution_name = f"{current_code} - {match.group(1).strip()}"
            else:
                parts = full_text.split(current_code + " - ", 1)
                if len(parts) > 1:
                    remaining = parts[1]
                    next_code_match = re.search(r'\d{4} - ', remaining)
                    if next_code_match:
                        institution_name = f"{current_code} - {remaining[:next_code_match.start()].strip()}"
                    else:
                        institution_name = f"{current_code} - {remaining.strip()}"
                else:
                    institution_name = full_text
            
            insts.append({"CodR": codR, "CodEstab": current_code, "Nome": institution_name})
    return insts

def get_cursos(codR, codEstab):
    payload = {"CodR": codR, "CodEstab": codEstab, "listagem": "Lista de Colocados"}
    resp = session.post(LISTA_CURSOS_URL, data=payload)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    cursos = []
    for opt in soup.find_all("option"):
        val = opt.get("value")
        if val and val.strip().isdigit(): 

            full_text = opt.text.strip()
            current_code = val.strip()
            

            import re
            pattern = rf"{re.escape(current_code)} - ([^A-Z0-9L]+?)(?=[A-Z]?\d{{3,4}} - |\s*$)"
            match = re.search(pattern, full_text)
            
            if match:
                course_name = f"{current_code} - {match.group(1).strip()}"
            else:
                parts = full_text.split(current_code + " - ", 1)
                if len(parts) > 1:
                    remaining = parts[1]
                    next_code_match = re.search(r'[A-Z]?\d{3,4} - ', remaining)
                    if next_code_match:
                        course_name = f"{current_code} - {remaining[:next_code_match.start()].strip()}"
                    else:
                        course_name = f"{current_code} - {remaining.strip()}"
                else:
                    course_name = full_text
            
            cursos.append({"CodCurso": current_code, "NomeCurso": course_name})
    return cursos

def get_colocados(codR, codEstab, codCurso):
    payload = {"CodR": codR, "CodEstab": codEstab, "CodCurso": codCurso, "search": "Continuar"}
    print(f"   [DEBUG] POST para colocados: CodR={codR}, CodEstab={codEstab}, CodCurso={codCurso}")
    resp = session.post(LISTA_COL_URL, data=payload)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    tables = soup.find_all("table")
    colocados = []
    seen_students = set()  
    
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:

                id_cell = cells[0].get_text(strip=True)
                name_cell = cells[1].get_text(strip=True)
                
                if "(" in id_cell and ")" in id_cell and any(c.isdigit() for c in id_cell):
                    if name_cell and len(name_cell) > 3 and any(c.isalpha() for c in name_cell):
                        if "Nome" not in name_cell and "Identificação" not in name_cell:
                            student_key = f"{id_cell}|{name_cell}"
                            if student_key not in seen_students:
                                colocados.append({"id": id_cell, "nome": name_cell})
                                seen_students.add(student_key)
    
    return colocados


def append_to_csv(universidade, curso, colocados, filename="AlunosColocados.csv"):
    if not colocados:
        return

    data_to_add = []
    for colocado in colocados:
        data_to_add.append({
            "Universidade": universidade,
            "Curso": curso,
            "Nº Identificação": colocado["id"],
            "Nome": colocado["nome"]
        })
    
    df_new = pd.DataFrame(data_to_add)
    
    if os.path.exists(filename):
        df_new.to_csv(filename, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(filename, mode='w', header=True, index=False, encoding='utf-8-sig')

    print(f" {len(colocados)} colocados salvos no CSV")

def main():
    csv_filename = "AlunosColocados.csv"
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
    
    total_colocados = 0
    
    for tipo in TIPOS_INSTITUICAO:
        codR = tipo["CodR"]
        insts = get_instituicoes(codR)
        print(f"\n=== {tipo['Tipo']}s encontradas: {len(insts)} ===\n")
        for inst in insts:
            print(f"🔹 {inst['Nome']} ({inst['CodEstab']})")
            cursos = get_cursos(codR, inst["CodEstab"])
            if not cursos:
                print(" Nenhum curso encontrado")
                continue
            for curso in cursos:
                print(f"➡️ Curso: {curso['NomeCurso']} | CodCurso: {curso['CodCurso']}")
                try:
                    colocados = get_colocados(codR, inst["CodEstab"], curso["CodCurso"])
                    if colocados:
                        for colocado in colocados:
                            print(f"   {colocado['id']} | {colocado['nome']}")
                        
                        append_to_csv(inst['Nome'], curso['NomeCurso'], colocados, csv_filename)
                        total_colocados += len(colocados)
                    else:
                        print(" Nenhum colocado encontrado")
                except Exception as e:
                    print(f" Erro : {e}")
                time.sleep(DELAY)
    

if __name__ == "__main__":
    main()
