"""Master automated test runner and verification auditor for ATS TCS Peru."""
import sys
import time
import subprocess
from pathlib import Path


def run_command(cmd, desc):
    print(f"\n{'='*75}")
    print(f"[*] {desc}")
    print(f"    Comando: {' '.join(cmd)}")
    print(f"{'='*75}")
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    dt = time.time() - t0
    print(res.stdout)
    if res.stderr:
        print(f"[STDERR]:\n{res.stderr}")
    print(f"[STATUS]: {'PASSED' if res.returncode == 0 else 'FAILED'} (Tiempo: {dt:.2f}s)")
    return res.returncode == 0


def main():
    print("\n" + "#"*75)
    print("# SISTEMA ATS TCS PERÚ - VERIFICACIÓN Y AUDITORÍA INTEGRAL DE EXTREMO A EXTREMO")
    print("#"*75)

    py_exe = sys.executable

    phases = [
        (
            [py_exe, "-m", "pytest", "tests/contract", "-v"],
            "FASE 1: Pruebas de Contratos, DDL, Triggers de Inmutabilidad y Esquemas Pydantic",
        ),
        (
            [py_exe, "-m", "pytest", "tests/unit", "-v"],
            "FASE 2: Pruebas Unitarias, Seguridad RBAC, Resiliencia, Algoritmos y UI con AppTest",
        ),
        (
            [py_exe, "-m", "pytest", "tests/integration", "-v"],
            "FASE 3: Pruebas de Integración, Ciclos de Vida, Batch Ingest y Flujo End-to-End",
        ),
        (
            [py_exe, "-m", "pytest", "--cov=src", "--cov-report=term-missing"],
            "FASE 4: Auditoría Consolidada de Cobertura Global de Código",
        ),
    ]

    all_passed = True
    for cmd, desc in phases:
        ok = run_command(cmd, desc)
        if not ok:
            all_passed = False
            print(f"\n[ERROR CRÍTICO] La fase '{desc}' no superó todas las aserciones.")
            break

    print("\n" + "="*75)
    if all_passed:
        print(">>> RESULTADO AUDITORÍA: 100% DE PRUEBAS SUPERADAS EXITOSAMENTE <<<")
        print(">>> TODAS LAS FUNCIONALIDADES DEL SISTEMA FUNCIONAN SEGÚN LO ESPERADO <<<")
    else:
        print(">>> RESULTADO AUDITORÍA: SE ENCONTRARON FALLOS EN LA EJECUCIÓN <<<")
    print("="*75 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
