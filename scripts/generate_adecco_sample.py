"""Generate sample Adecco Excel file with 20 calibrated rows."""
from pathlib import Path
import pandas as pd

data = [
    # 7 Red Duplicates
    {"DNI / CE": "76128709", "Nombres y Apellidos": "Diego Alonso Ramos Quispe", "Móvil": "989322088", "Puesto": "Desarrollador Java Senior", "Correo": "diego.ramos@gmail.com"},
    {"DNI / CE": "45892134", "Nombres y Apellidos": "Jorge Luis Chavez Pinto", "Móvil": "987654321", "Puesto": "Cloud Architect", "Correo": "jorge.chavez@gmail.com"},
    {"DNI / CE": "71984512", "Nombres y Apellidos": "Valeria Beatriz Flores Rodriguez", "Móvil": "976543210", "Puesto": "Full Stack Developer", "Correo": "valeria.flores@gmail.com"},
    {"DNI / CE": "70812390", "Nombres y Apellidos": "Miguel Angel Torres Huaman", "Móvil": "965432109", "Puesto": "QA Automation", "Correo": "miguel.torres@gmail.com"},
    {"DNI / CE": "47589623", "Nombres y Apellidos": "Patricia Elena Vargas Delgado", "Móvil": "954321098", "Puesto": "Scrum Master", "Correo": "patricia.vargas@gmail.com"},
    {"DNI / CE": "73412589", "Nombres y Apellidos": "Renzo Paolo Castillo Morales", "Móvil": "943210987", "Puesto": "Backend Python Developer", "Correo": "renzo.castillo@gmail.com"},
    {"DNI / CE": "48912345", "Nombres y Apellidos": "Monica Beatriz Rojas Soto", "Móvil": "932109876", "Puesto": "Frontend Angular Specialist", "Correo": "monica.rojas@gmail.com"},
    # 3 Yellow Reactivables (>180 days)
    {"DNI / CE": "74890123", "Nombres y Apellidos": "Sebastian Andres Lopez Herrera", "Móvil": "921098765", "Puesto": "Mobile Developer Flutter", "Correo": "sebastian.lopez@gmail.com"},
    {"DNI / CE": "43981276", "Nombres y Apellidos": "Lucia Esperanza Benitez Navarro", "Móvil": "910987654", "Puesto": "Security Engineer", "Correo": "lucia.benitez@gmail.com"},
    {"DNI / CE": "75619283", "Nombres y Apellidos": "Gonzalo Martin Palacios Vega", "Móvil": "909876543", "Puesto": "Data Analyst", "Correo": "gonzalo.palacios@gmail.com"},
    # 8 Green Clean Inéditos
    {"DNI / CE": "80112233", "Nombres y Apellidos": "Brenda Sofia Gutierrez Paredes", "Móvil": "911223344", "Puesto": "Desarrollador Java", "Correo": "brenda.gutierrez@adecco-post.pe"},
    {"DNI / CE": "80223344", "Nombres y Apellidos": "Victor Manuel Romero Diaz", "Móvil": "922334455", "Puesto": "Data Engineer", "Correo": "victor.romero@adecco-post.pe"},
    {"DNI / CE": "80334455", "Nombres y Apellidos": "Camila Andrea Morales Rios", "Móvil": "933445566", "Puesto": "DevOps Specialist", "Correo": "camila.morales@adecco-post.pe"},
    {"DNI / CE": "80445566", "Nombres y Apellidos": "Andres Felipe Salazar Castro", "Móvil": "944556677", "Puesto": "Cloud Architect", "Correo": "andres.salazar@adecco-post.pe"},
    {"DNI / CE": "80556677", "Nombres y Apellidos": "Daniela Alejandra Ponce Vega", "Móvil": "955667788", "Puesto": "Full Stack Developer", "Correo": "daniela.ponce@adecco-post.pe"},
    {"DNI / CE": "80667788", "Nombres y Apellidos": "Mateo Nicolas Cardenas Ruiz", "Móvil": "966778899", "Puesto": "QA Automation", "Correo": "mateo.cardenas@adecco-post.pe"},
    {"DNI / CE": "80778899", "Nombres y Apellidos": "Lucia Fernanda Tapia Cruz", "Móvil": "977889900", "Puesto": "Scrum Master", "Correo": "lucia.tapia@adecco-post.pe"},
    {"DNI / CE": "80889900", "Nombres y Apellidos": "Gabriel Alejandro Vidal Ortiz", "Móvil": "988990011", "Puesto": "Backend Python Developer", "Correo": "gabriel.vidal@adecco-post.pe"},
    # 2 Purple Alumni TCS
    {"DNI / CE": "46753314", "Nombres y Apellidos": "Carlos Eduardo Garcia Sanchez", "Móvil": "999001122", "Puesto": "Tech Lead Java", "Correo": "carlos.garcia@adecco-post.pe"},
    {"DNI / CE": "41239876", "Nombres y Apellidos": "Raul Fernando Munoz Arias", "Móvil": "911002233", "Puesto": "Senior Cloud Engineer", "Correo": "raul.munoz@adecco-post.pe"},
]

df = pd.DataFrame(data)
out_path = Path(__file__).parent.parent / "data" / "Adecco_Semana_37.xlsx"
df.to_excel(out_path, index=False)
print(f"Generated {out_path} with {len(df)} rows.")
