"""Pacotes compactados e detecção de formato dos CSVs.

Os microdados vêm em .zip e, para 2019-2021, em .rar. O .zip é lido pela
biblioteca padrão; o .rar exige o 7-Zip, que também é usado para .zip quando
está instalado por ser bem mais rápido em arquivos de centenas de megabytes.
"""
from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

_CAMINHOS_7ZIP = (
    Path("C:/Program Files/7-Zip/7z.exe"),
    Path("C:/Program Files (x86)/7-Zip/7z.exe"),
)
AUTO = "auto"


def localizar_7zip() -> Path | None:
    for nome in ("7z", "7za", "7zz"):
        achado = shutil.which(nome)
        if achado:
            return Path(achado)
    return next((p for p in _CAMINHOS_7ZIP if p.exists()), None)


def _resolver(sete_zip) -> Path | None:
    return localizar_7zip() if sete_zip == AUTO else sete_zip


def _exige_7zip(pacote: Path) -> RuntimeError:
    return RuntimeError(f"{pacote.name}: abrir este formato requer o 7-Zip instalado (https://www.7-zip.org)")


def listar(pacote: str | Path, sete_zip=AUTO) -> list[str]:
    """Nomes dos arquivos dentro do pacote (sem as pastas)."""
    pacote, sete = Path(pacote), _resolver(sete_zip)
    if sete:
        saida = subprocess.run([str(sete), "l", "-slt", "-ba", "-sccUTF-8", str(pacote)],
                               capture_output=True, check=True).stdout.decode("utf-8", "replace")
        membros, atual = [], {}
        for linha in saida.splitlines() + [""]:
            if not linha.strip():
                if atual.get("Path") and atual.get("Folder", "-") != "+" and "Attributes" in atual \
                        and not atual["Attributes"].startswith("D"):
                    membros.append(atual["Path"].replace("\\", "/"))
                atual = {}
                continue
            chave, _, valor = linha.partition(" = ")
            atual[chave.strip()] = valor.strip()
        return membros
    if pacote.suffix.lower() == ".zip":
        with zipfile.ZipFile(pacote) as z:
            return [i.filename for i in z.infolist() if not i.is_dir()]
    raise _exige_7zip(pacote)


def extrair(pacote: str | Path, membro: str, destino_dir: str | Path, sete_zip=AUTO) -> Path:
    """Extrai um único arquivo do pacote para destino_dir, sem a estrutura de pastas."""
    pacote, destino_dir, sete = Path(pacote), Path(destino_dir), _resolver(sete_zip)
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / Path(membro).name
    if sete:
        subprocess.run([str(sete), "e", "-y", f"-o{destino_dir}", str(pacote), membro],
                       check=True, stdout=subprocess.DEVNULL)
        return destino
    if pacote.suffix.lower() == ".zip":
        with zipfile.ZipFile(pacote) as z, z.open(membro) as origem, open(destino, "wb") as saida:
            shutil.copyfileobj(origem, saida, 1 << 20)
        return destino
    raise _exige_7zip(pacote)


def detectar_encoding(caminho: str | Path, amostra: int = 1 << 20) -> str:
    """'utf-8' ou 'latin-1'. Tolera caractere multibyte cortado no fim da amostra."""
    dados = Path(caminho).read_bytes()[:amostra]
    try:
        dados.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError as erro:
        return "utf-8" if erro.start >= len(dados) - 3 and len(dados) == amostra else "latin-1"


def detectar_separador(caminho: str | Path) -> str:
    enc = detectar_encoding(caminho)
    with open(caminho, encoding=enc, errors="replace") as f:
        cabecalho = f.readline()
    return max((";", "|", ",", "\t"), key=cabecalho.count)
