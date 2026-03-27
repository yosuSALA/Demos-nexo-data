"""
app.py — Ventana principal del Motor Analítico ETL Super Cías
==============================================================
Interfaz simplificada que permite:
  1. Seleccionar la ruta de la base de datos DuckDB de destino.
  2. Elegir entre actualizar la base existente o crear una nueva.
  3. Ejecutar el proceso ETL (descarga, filtrado, carga) con un clic.
  4. Programar la ejecución automática mensual.

La descarga del ZIP de la Super Cías y el filtrado del sector fiduciario
se ejecutan automáticamente — no se requiere archivo de origen.
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from gui.backend import ETLResult, get_high_water_mark, get_record_count, run_etl
from gui.config_manager import load_config, save_config

# ──────────────────────────────────────────────
# Constantes de diseño
# ──────────────────────────────────────────────
NOMBRE_CONSULTORA = "Fiducia Consulting Group"
TITULO_APP = f"Motor Analítico ETL — Super Cías — {NOMBRE_CONSULTORA}"
ANCHO_VENTANA = 900
ALTO_VENTANA = 680
FUENTE_TITULO = ("Segoe UI", 18, "bold")
FUENTE_SECCION = ("Segoe UI", 14, "bold")
FUENTE_NORMAL = ("Segoe UI", 12)
FUENTE_PEQUEÑA = ("Segoe UI", 10)
PAD = 12


class ETLApp(ctk.CTk):
    """Ventana principal del Motor Analítico ETL."""

    def __init__(self) -> None:
        super().__init__()

        self.title(TITULO_APP)
        self.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}")
        self.minsize(800, 600)
        self.resizable(True, True)

        # Estado
        self.config_data = load_config()
        self._etl_en_ejecucion = False

        # Tema
        ctk.set_appearance_mode(self.config_data.get("tema", "dark"))
        ctk.set_default_color_theme("blue")

        self._crear_interfaz()
        self._cargar_valores_guardados()
        self._actualizar_info_db()

    # ──────────────────────────────────────────
    # Construcción de la interfaz
    # ──────────────────────────────────────────
    def _crear_interfaz(self) -> None:
        self._main_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self._main_frame.pack(fill="both", expand=True)
        self._main_frame.columnconfigure(0, weight=1)

        fila = 0
        fila = self._crear_encabezado(fila)
        fila = self._crear_seccion_destino(fila)
        fila = self._crear_seccion_modo(fila)
        fila = self._crear_seccion_programacion(fila)
        fila = self._crear_seccion_ejecucion(fila)
        fila = self._crear_barra_estado(fila)

    # ── Encabezado ────────────────────────────
    def _crear_encabezado(self, fila: int) -> int:
        frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        frame.grid(row=fila, column=0, sticky="ew", padx=PAD, pady=(PAD, 4))
        frame.columnconfigure(1, weight=1)

        # Logo
        logo = ctk.CTkFrame(frame, width=56, height=56, corner_radius=8,
                            fg_color=("#2563EB", "#1E40AF"))
        logo.grid(row=0, column=0, rowspan=2, padx=(0, PAD), pady=4)
        logo.grid_propagate(False)
        ctk.CTkLabel(logo, text="SC", font=("Segoe UI", 22, "bold"),
                     text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="Motor Analítico ETL — Super Cías",
                     font=FUENTE_TITULO, anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(frame, text=NOMBRE_CONSULTORA,
                     font=FUENTE_NORMAL, text_color="gray", anchor="w").grid(
            row=1, column=1, sticky="w")

        # Selector de tema
        self._var_tema = ctk.StringVar(value=self.config_data.get("tema", "dark"))
        ctk.CTkOptionMenu(
            frame, values=["dark", "light", "system"],
            variable=self._var_tema, width=100,
            command=self._cambiar_tema,
        ).grid(row=0, column=2, rowspan=2, padx=(PAD, 0))

        # Info de la base de datos
        info = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        info.grid(row=fila + 1, column=0, sticky="ew", padx=PAD, pady=(4, PAD))
        info.columnconfigure((0, 1, 2), weight=1)

        self._lbl_hwm = ctk.CTkLabel(info, text="Última carga: —", font=FUENTE_PEQUEÑA)
        self._lbl_hwm.grid(row=0, column=0, sticky="w")

        self._lbl_registros = ctk.CTkLabel(info, text="Registros: —", font=FUENTE_PEQUEÑA)
        self._lbl_registros.grid(row=0, column=1)

        self._lbl_db_path = ctk.CTkLabel(info, text="DB: —",
                                         font=FUENTE_PEQUEÑA, text_color="gray")
        self._lbl_db_path.grid(row=0, column=2, sticky="e")

        return fila + 2

    # ── Base de datos destino ─────────────────
    def _crear_seccion_destino(self, fila: int) -> int:
        frame = self._seccion(fila, "Base de Datos de Destino")
        frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Archivo DuckDB:",
                     font=FUENTE_NORMAL).grid(row=0, column=0, sticky="w", pady=4)
        self._entry_db = ctk.CTkEntry(
            frame, placeholder_text="output/sib_final.duckdb", font=FUENTE_NORMAL)
        self._entry_db.grid(row=0, column=1, sticky="ew", padx=(8, 4), pady=4)
        ctk.CTkButton(frame, text="Explorar", width=90,
                      command=self._seleccionar_db).grid(row=0, column=2, pady=4)

        # Nota explicativa
        ctk.CTkLabel(
            frame,
            text=(
                "Los datos se descargan automáticamente desde el portal de la Super Cías. "
                "Solo necesita indicar dónde guardar la base de datos resultante."
            ),
            font=FUENTE_PEQUEÑA, text_color="gray", wraplength=700, justify="left",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 4))

        return fila + 1

    # ── Modo de ejecución ─────────────────────
    def _crear_seccion_modo(self, fila: int) -> int:
        frame = self._seccion(fila, "Modo de Ejecución")

        self._var_modo = ctk.StringVar(value="update")

        ctk.CTkRadioButton(
            frame,
            text="Actualizar Base Existente (agrega solo datos nuevos sin duplicar)",
            variable=self._var_modo, value="update",
            font=FUENTE_NORMAL,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=4)

        ctk.CTkRadioButton(
            frame,
            text="Crear Nueva Base de Datos (elimina la tabla anterior y recrea desde cero)",
            variable=self._var_modo, value="create",
            font=FUENTE_NORMAL,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=4)

        # Nota sobre el filtro automático
        ctk.CTkLabel(
            frame,
            text=(
                "Filtro automático: solo se cargan empresas del sector "
                "\"Administradora de Fondos y Fideicomisos\"."
            ),
            font=FUENTE_PEQUEÑA, text_color=("#059669", "#34D399"),
            wraplength=700, justify="left",
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        return fila + 1

    # ── Programación ──────────────────────────
    def _crear_seccion_programacion(self, fila: int) -> int:
        frame = self._seccion(fila, "Programación — Ejecución Automática Mensual")
        frame.columnconfigure(3, weight=1)

        ctk.CTkLabel(frame, text="Día del mes:",
                     font=FUENTE_NORMAL).grid(row=0, column=0, sticky="w", pady=4)
        self._spin_dia = ctk.CTkOptionMenu(
            frame, values=[str(d) for d in range(1, 29)], width=70)
        self._spin_dia.grid(row=0, column=1, padx=(8, 16), pady=4)

        ctk.CTkLabel(frame, text="Hora (HH:MM):",
                     font=FUENTE_NORMAL).grid(row=0, column=2, sticky="w", pady=4)
        self._entry_hora = ctk.CTkEntry(frame, width=80, placeholder_text="09:00",
                                        font=FUENTE_NORMAL)
        self._entry_hora.grid(row=0, column=3, sticky="w", padx=(8, 16), pady=4)

        self._var_programacion = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            frame, text="Activar programación",
            variable=self._var_programacion, font=FUENTE_NORMAL,
            command=self._toggle_programacion,
        ).grid(row=0, column=4, padx=(8, 0), pady=4)

        self._lbl_estado_prog = ctk.CTkLabel(
            frame, text="Estado: Inactivo", font=FUENTE_PEQUEÑA,
            text_color=("#B91C1C", "#F87171"),
        )
        self._lbl_estado_prog.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 4))

        ctk.CTkLabel(
            frame,
            text=(
                "Nota: Para ejecución confiable cuando la aplicación está cerrada, "
                "configure Windows Task Scheduler con el botón de abajo."
            ),
            font=FUENTE_PEQUEÑA, text_color="gray", wraplength=700, justify="left",
        ).grid(row=2, column=0, columnspan=5, sticky="w", pady=(0, 4))

        ctk.CTkButton(
            frame, text="Copiar Comando Task Scheduler", width=240,
            fg_color=("#6B7280", "#4B5563"),
            command=self._copiar_comando_task_scheduler,
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 4))

        return fila + 1

    # ── Ejecución ─────────────────────────────
    def _crear_seccion_ejecucion(self, fila: int) -> int:
        frame = self._seccion(fila, "Ejecución Manual")
        frame.columnconfigure(0, weight=1)

        self._btn_ejecutar = ctk.CTkButton(
            frame, text="Ejecutar Actualización Ahora",
            font=("Segoe UI", 16, "bold"), height=50,
            fg_color=("#2563EB", "#1D4ED8"),
            hover_color=("#1D4ED8", "#1E40AF"),
            command=self._iniciar_etl,
        )
        self._btn_ejecutar.grid(row=0, column=0, sticky="ew", pady=(0, PAD))

        self._progress_bar = ctk.CTkProgressBar(frame, height=16)
        self._progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        self._progress_bar.set(0)

        self._lbl_estado = ctk.CTkLabel(
            frame, text="Listo para ejecutar.", font=FUENTE_NORMAL, anchor="w")
        self._lbl_estado.grid(row=2, column=0, sticky="w")

        self._text_resultado = ctk.CTkTextbox(
            frame, height=130, font=FUENTE_PEQUEÑA, state="disabled")
        self._text_resultado.grid(row=3, column=0, sticky="ew", pady=(PAD, 0))

        return fila + 1

    # ── Barra de estado inferior ──────────────
    def _crear_barra_estado(self, fila: int) -> int:
        frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        frame.grid(row=fila, column=0, sticky="ew", padx=PAD, pady=(4, PAD))
        frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Motor Analítico ETL v2.0 — Polars + DuckDB — Descarga directa Super Cías",
            font=FUENTE_PEQUEÑA, text_color="gray",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(frame, text="Guardar Configuración", width=160,
                      fg_color=("#059669", "#047857"),
                      command=self._guardar_config).grid(row=0, column=1)

        return fila + 1

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────
    def _seccion(self, fila: int, titulo: str) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(self._main_frame)
        outer.grid(row=fila, column=0, sticky="ew", padx=PAD, pady=(0, PAD))
        outer.columnconfigure(0, weight=1)

        ctk.CTkLabel(outer, text=titulo, font=FUENTE_SECCION, anchor="w").grid(
            row=0, column=0, sticky="w", padx=PAD, pady=(PAD, 4))

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.grid(row=1, column=0, sticky="ew", padx=PAD, pady=(0, PAD))
        inner.columnconfigure(1, weight=1)
        return inner

    def _seleccionar_db(self) -> None:
        """Abre diálogo para seleccionar o crear el archivo DuckDB."""
        ruta = filedialog.asksaveasfilename(
            title="Seleccionar base de datos de destino",
            defaultextension=".duckdb",
            filetypes=[("DuckDB", "*.duckdb"), ("Todos", "*.*")],
        )
        if ruta:
            self._entry_db.delete(0, "end")
            self._entry_db.insert(0, ruta)
            self._actualizar_info_db()

    # ──────────────────────────────────────────
    # Lógica ETL
    # ──────────────────────────────────────────
    def _iniciar_etl(self) -> None:
        if self._etl_en_ejecucion:
            messagebox.showwarning(
                "ETL en curso",
                "Ya hay un proceso ETL ejecutándose. Espere a que finalice.",
            )
            return

        ruta_db = self._entry_db.get().strip() or "output/sib_final.duckdb"
        modo = self._var_modo.get()

        # Confirmar si el modo es "create" y ya existe la base
        if modo == "create" and Path(ruta_db).exists():
            confirmar = messagebox.askyesno(
                "Confirmar creación",
                f"El archivo ya existe:\n{ruta_db}\n\n"
                "Se eliminará la tabla existente y se recreará desde cero.\n"
                "¿Desea continuar?",
            )
            if not confirmar:
                return

        # Preparar GUI
        self._etl_en_ejecucion = True
        self._btn_ejecutar.configure(state="disabled", text="Ejecutando...")
        self._progress_bar.set(0)
        self._lbl_estado.configure(text="Iniciando proceso ETL...")
        self._limpiar_resultado()

        hilo = threading.Thread(
            target=self._ejecutar_etl_hilo,
            args=(Path(ruta_db), modo),
            daemon=True,
        )
        hilo.start()

    def _ejecutar_etl_hilo(self, db_path: Path, mode: str) -> None:
        try:
            resultado = run_etl(
                duckdb_path=db_path,
                mode=mode,
                on_progress=self._on_progress_callback,
            )
            self.after(0, self._etl_finalizado, resultado)
        except Exception as e:
            resultado = ETLResult(exitoso=False, mensaje_error=str(e))
            self.after(0, self._etl_finalizado, resultado)

    def _on_progress_callback(self, mensaje: str, porcentaje: float) -> None:
        self.after(0, self._actualizar_progreso, mensaje, porcentaje)

    def _actualizar_progreso(self, mensaje: str, porcentaje: float) -> None:
        self._progress_bar.set(porcentaje)
        self._lbl_estado.configure(text=mensaje)

    def _etl_finalizado(self, resultado: ETLResult) -> None:
        self._etl_en_ejecucion = False
        self._btn_ejecutar.configure(state="normal", text="Ejecutar Actualización Ahora")

        if resultado.exitoso:
            self._progress_bar.set(1.0)
            self._lbl_estado.configure(text="Proceso finalizado exitosamente.")
            resumen = (
                f"{'═' * 50}\n"
                f"  RESUMEN DE EJECUCIÓN ETL\n"
                f"{'═' * 50}\n"
                f"  Filas leídas      : {resultado.filas_leidas:>12,}\n"
                f"  Filas cargadas    : {resultado.filas_cargadas:>12,}\n"
                f"  Filas descartadas : {resultado.filas_descartadas:>12,}\n"
                f"  Duración          : {resultado.duracion_seg:>10.1f} seg\n"
                f"{'═' * 50}\n"
                f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
        else:
            self._progress_bar.set(0)
            self._lbl_estado.configure(text=f"Error: {resultado.mensaje_error}")
            resumen = f"ERROR EN EL PROCESO ETL:\n{resultado.mensaje_error}"

        self._escribir_resultado(resumen)
        self._actualizar_info_db()

    def _limpiar_resultado(self) -> None:
        self._text_resultado.configure(state="normal")
        self._text_resultado.delete("1.0", "end")
        self._text_resultado.configure(state="disabled")

    def _escribir_resultado(self, texto: str) -> None:
        self._text_resultado.configure(state="normal")
        self._text_resultado.delete("1.0", "end")
        self._text_resultado.insert("1.0", texto)
        self._text_resultado.configure(state="disabled")

    # ──────────────────────────────────────────
    # Info de la base de datos
    # ──────────────────────────────────────────
    def _actualizar_info_db(self) -> None:
        ruta_db = self._entry_db.get().strip() if hasattr(self, "_entry_db") else ""
        db_path = Path(ruta_db) if ruta_db else Path(self.config_data.get("ruta_db", ""))

        hwm = get_high_water_mark(db_path)
        count = get_record_count(db_path)

        self._lbl_hwm.configure(text=f"Última carga: {hwm or '—'}")
        self._lbl_registros.configure(text=f"Registros: {count:,}" if count else "Registros: —")
        self._lbl_db_path.configure(text=f"DB: {db_path}")

    # ──────────────────────────────────────────
    # Programación
    # ──────────────────────────────────────────
    def _toggle_programacion(self) -> None:
        if self._var_programacion.get():
            dia = self._spin_dia.get()
            hora = self._entry_hora.get().strip() or "09:00"
            self._lbl_estado_prog.configure(
                text=f"Estado: Activo — Día {dia} de cada mes a las {hora}",
                text_color=("#059669", "#34D399"),
            )
        else:
            self._lbl_estado_prog.configure(
                text="Estado: Inactivo",
                text_color=("#B91C1C", "#F87171"),
            )

    def _copiar_comando_task_scheduler(self) -> None:
        dia = self._spin_dia.get()
        hora = self._entry_hora.get().strip() or "09:00"
        python_exe = Path(".\\.venv\\Scripts\\python.exe").resolve()
        script = Path("main_gui.py").resolve()

        comando = (
            f'schtasks /create /tn "ETL_SuperCias_Mensual" '
            f'/tr "{python_exe} {script} --auto" '
            f'/sc monthly /d {dia} /st {hora} '
            f'/rl HIGHEST /f'
        )

        self.clipboard_clear()
        self.clipboard_append(comando)
        messagebox.showinfo(
            "Comando copiado",
            f"Comando copiado al portapapeles:\n\n{comando}\n\n"
            "Ejecútelo en una terminal con permisos de Administrador.",
        )

    # ──────────────────────────────────────────
    # Tema
    # ──────────────────────────────────────────
    def _cambiar_tema(self, tema: str) -> None:
        ctk.set_appearance_mode(tema)
        self.config_data["tema"] = tema

    # ──────────────────────────────────────────
    # Persistencia
    # ──────────────────────────────────────────
    def _guardar_config(self) -> None:
        self.config_data.update({
            "ruta_db": self._entry_db.get(),
            "modo": self._var_modo.get(),
            "programacion_dia": int(self._spin_dia.get()),
            "programacion_hora": self._entry_hora.get(),
            "programacion_activa": self._var_programacion.get(),
            "tema": self._var_tema.get(),
        })
        save_config(self.config_data)
        messagebox.showinfo("Configuración guardada",
                            "La configuración fue guardada exitosamente.")

    def _cargar_valores_guardados(self) -> None:
        cfg = self.config_data

        if cfg.get("ruta_db"):
            self._entry_db.insert(0, cfg["ruta_db"])

        self._var_modo.set(cfg.get("modo", "update"))

        self._spin_dia.set(str(cfg.get("programacion_dia", 5)))
        if cfg.get("programacion_hora"):
            self._entry_hora.insert(0, cfg["programacion_hora"])
        self._var_programacion.set(cfg.get("programacion_activa", False))
        self._toggle_programacion()
