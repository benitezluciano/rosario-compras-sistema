# Controlador: `reparto_controller.py`

## Propósito Principal
Es el orquestador inteligente transaccional que pauta y define la secuencia metodológica exacta de pasos obligados para completar con éxito el complejo Caso de Uso 2 (Reparto Automático). Adicionalmente, posee facultades lógicas para pausar el motor interno y gestionar decisiones interactuando directamente con el usuario operativo cuando surgen bloqueos de quiebres de stock.

## Dependencias e Interacciones
- **Llama a**: `RepartoModel` (cálculos transaccionales y prorrateo) y `RepartoView` (dibujo de UI).
- **Es llamado por**: `main.py` (durante la inicialización de módulos generales).

## Lógica Clave
- **Flujo Maestro de Asignación Logística (`procesar_asignacion`)**:
  - Al iniciar el pulso o llamado humano, cambia inmediatamente el estado visual dinámico en la UI mutando la bandera hacia la etiqueta "Procesando...".
  - Dispara en su modelo atado la orden `validar_stock_vs_pedidos()` para forzar un análisis matemático especulativo o en "crudo" del catálogo. Este análisis se realiza sin efectuar ni comprometer reducciones tempranas (mermas físicas prematuras) sobre la Base de Datos general.
  - **Intercepción Compleja del Flujo Base (Excepción E1)**: Si el controlador detecta que el modelo le ha inyectado o reportado el indicador o bandera algorítmica de discrepancia (lo que significa que la demanda general supera o rebasa físicamente el material consolidable en depósito), paraliza suspensivamente la cadena transaccional base y lanza su propia sub-rutina de mitigación invocando en su vista la orden de detención visual interactiva (`mostrar_alerta_ajuste(discrepancias)`).
    - **Caso de aborto (Si el humano cancela)**: Transiciona su propia etiqueta final en la Vista hacia un estado literal de "Asignación Cancelada" y corta o frena instantáneamente su cadena impidiendo modificaciones colaterales.
    - **Caso resolutivo (Si el humano acepta)**: Extrae meticulosamente las ramas y ramificaciones del sub-diccionario exacto correspondiente a los "ajustes matemáticos" (sugeridos nativamente por el Modelo) para desempaquetarlo y enviarlo entonces de manera formal, explícita y pautada, encajado como parámetro dict de sustitución maestra, hacia el comando consolidado final `ejecutar_reparto_masivo` que inyectará físicamente los remitos finales.
  - Tras lograr concluir el flujo sin colapsos colaterales y ya sea por el camino directo y normal, o luego de la superación resolutiva interactiva en la Excepción E1, instruye a su propia cadena un refresco nativo en la consola invocando cíclicamente de forma silenciosa la recarga de grilla inicial en la función interna `inicializar()`.
