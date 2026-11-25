# Contenido de las diapositivas (para Gamma)

Presentación del 27/11/2026. Grupo de 4, 10 minutos como máximo, enfoque de negocio ante la dirección de Rosario Compras.

Este archivo tiene tres partes:
- **Parte A:** el texto que se pega en Gamma. Es lo único que va dentro de la herramienta.
- **Parte B:** las notas del orador, el reparto de tiempos y las preguntas probables. No se pega en Gamma.
- **Parte C:** los puntos que el grupo tiene que confirmar antes de presentar.

Fuentes: documentos 02 a 06 de `documentacion/` y decisiones DEC-004 a DEC-025 de `gestion/DECISIONES.md`.

---

## Cómo usarlo en Gamma (para Sergio)

1. En Gamma, elegir crear una **presentación** pegando texto. Si Gamma ofrece conservar el texto tal cual en lugar de reescribirlo o resumirlo, elegir esa opción (a verificar en la pantalla).
2. Formato 16:9, idioma español, tono profesional y sobrio.
3. Pegar la Parte A completa. Las diapositivas están separadas por `---`.
4. En las instrucciones adicionales, pegar este texto:

> Presentación ejecutiva en español, formato 16:9, de exactamente 10 diapositivas, una por cada sección separada por ---. Conservá el texto de cada sección. No agregues diapositivas, datos, cifras ni porcentajes que no estén en el texto. Estilo sobrio y corporativo, tipografía grande y pocas palabras por diapositiva. Donde dice [IMAGEN: archivo] dejá el espacio libre: la imagen la sube una persona. No generes ilustraciones, gráficos ni capturas de pantalla inventadas.

5. Subir a mano las imágenes que están en `presentacion/diagramas/`:
   - `as-is.png` y `to-be.png` (diapositivas 3 y 5).
6. **Revisar después de generar:** que haya 10 diapositivas, que no aparezcan cifras que no estén abajo, que las estimaciones sigan rotuladas como estimaciones y que ningún texto quede cortado.
7. **El video** (diapositiva 7) conviene reproducirlo desde el reproductor del equipo y no incrustarlo, para no depender de la conexión del aula.

---

# PARTE A: TEXTO PARA PEGAR EN GAMMA

# Rosario Compras: del pedido al remito, sin planillas

Propuesta de mejora del circuito de compras y reparto

[Integrantes del grupo] · [Materia] · 27 de noviembre de 2026

---

# Una compra conjunta que funciona

Rosario Compras agrupa a 12 empresas supermercadistas, con 32 locales, que compran juntas para conseguir mejores precios.

- La negociación de precios con los proveedores funciona.
- El control físico de la mercadería funciona.
- El problema está en el tramo que va del pedido del socio al remito: depende de Excel por correo, planillas impresas y trabajo manual.

El desafío no es comprar mejor. Es consolidar los pedidos y repartir la mercadería sin planillas.

---

# Hoy: cuatro problemas entre el pedido y el remito

[IMAGEN: as-is.png, a la izquierda, ocupando toda la altura]

1. **Reparto manual.** Se reparte artículo por artículo y se tacha en planillas de papel. Hay errores de cantidades y socios olvidados.
2. **Planillas físicas y Excel.** Los pedidos llegan por correo, se imprimen y se unen a mano. Hay versiones duplicadas y pérdida de datos.
3. **Remitos tardíos.** Se emiten después del reparto manual y retrasan el armado de palets.
4. **Planillas sin formato estándar.** Cada socio usa su formato y eso genera errores de precios y cantidades.

---

# Lo que cuesta hoy

**~4 horas**
para repartir y armar un pedido

**+500 hojas**
de papel por mes

**~30 horas**
por semana que se podrían liberar

Estimaciones de la organización obtenidas en el relevamiento. No fueron medidas por el grupo.

---

# Mismo circuito, otro modo de trabajo

[IMAGEN: as-is.png y to-be.png, una al lado de la otra, ocupando casi toda la diapositiva]

El socio carga su pedido en el sistema. La consolidación, la orden de compra, el reparto y el remito se generan solos. Las personas siguen decidiendo.

---

# Qué cambia y qué no

**Se elimina**
- Impresión de las planillas de pedido
- Transcripción manual de las cantidades de los 12 socios
- Tachado en papel de lo ya repartido

**Se modifica**
- Pedido: del correo con Excel a la carga directa en el sistema
- Reparto: de manual a automático
- Remito: se emite apenas termina el reparto

**Se mantiene**
- Negociación de precios por los ejecutivos
- Control físico de la mercadería
- Carga de la factura y orden de pago

El módulo apoya el criterio de las personas, no lo reemplaza.

---

# El prototipo ya funciona de punta a punta

Video de 2 minutos con el recorrido completo:

1. El socio carga su pedido
2. El ejecutivo ve todo consolidado y ajusta cantidades
3. Se consolida y se genera la orden de compra
4. Recepción con doble control de cantidades y precios
5. Reparto automático con prorrateo ante faltantes
6. Remito en PDF y consulta del socio

Prueba integral del circuito: 13 de 13 verificaciones correctas. Los datos del video son de prueba.

---

# Por qué conviene

- **Reparto y armado de un pedido:** meta de reducirlo al menos un 70 % (de unas 4 horas a menos de 1 hora 12 minutos).
- **Discrepancias en pedidos y reparto:** meta de reducirlas al menos un 90 %.
- **Papel:** se elimina, porque la carga digital y los PDF lo reemplazan.
- **Tiempo liberado:** cerca de 30 horas por semana, unas 130 por mes.
- **Reparto equitativo:** una sola regla de prorrateo, igual para todos los socios.
- **Costo:** sin licencias de terceros en el prototipo y con la infraestructura existente.

Metas y cifras del relevamiento: se miden en el piloto. El retorno de la inversión se calcula con datos de la organización.

---

# Cómo se llega a producción

**Etapas:** E4 cierre de brechas críticas, E5 piloto con dos socios y, si el piloto funciona, integración con IT.

**Riesgos y cómo se cubren**
- Stock mal calculado tras una recepción: se corrige en E4, antes del piloto.
- Diferencias de precio o cantidad sin seguimiento: se corrige en E4.
- 20 usuarios simultáneos e integración con SAP: se resuelve en la integración con IT, con un motor central.
- Exposición de datos y credenciales de prueba: cifrado y manejo de secretos en la integración. El prototipo no se usa con datos reales.
- Que los beneficios no se alcancen en la práctica: el piloto los mide antes de la puesta en marcha.

---

# Qué le pedimos a la dirección

**Aprobar la etapa E4 y un piloto con dos socios.**

Es una inversión acotada que permite medir los beneficios con datos propios antes de comprometer la integración completa.

**Criterios de éxito del piloto**
- Reparto y armado: reducción de al menos el 70 % respecto de las 4 horas actuales
- Discrepancias: reducción de al menos el 90 %
- Papel del circuito: eliminado

Si se cumplen, se continúa con la integración. Si no, los resultados indican qué ajustar antes de invertir.

El problema está acotado, la solución ya existe como prototipo y los beneficios son medibles.

---

# PARTE B: NOTAS DEL ORADOR (no se pega en Gamma)

Los tiempos suman 9:15 y dejan unos 45 segundos de margen. Los nombres de los 4 integrantes están pendientes: se usan las letras A a D.

| # | Diapositiva | Quién | Tiempo |
| :--- | :--- | :--- | :--- |
| 1 | Portada | A | 0:10 |
| 2 | Una compra conjunta que funciona | A | 0:30 |
| 3 | Cuatro problemas | A | 1:15 |
| 4 | Lo que cuesta hoy | A | 0:30 |
| 5 | Mismo circuito, otro modo de trabajo | B | 1:15 |
| 6 | Qué cambia y qué no | B | 0:50 |
| 7 | Prototipo (video) | C | 2:10 |
| 8 | Por qué conviene | D | 1:10 |
| 9 | Cómo se llega a producción | D | 0:50 |
| 10 | Qué le pedimos a la dirección | D | 0:35 |

**1. Portada.** Saludar y decir en una frase qué se propone: "Vamos a mostrarles cómo pasar del pedido al remito sin planillas."

**2. Contexto.** "La compra conjunta ya funciona. Lo que se traba es el tramo que va del pedido del socio al remito. No venimos a cambiar cómo se negocia ni cómo se controla la mercadería."

**3. Problemas.** Recorrer el diagrama de arriba abajo con el dedo en las marcas 1 a 4. Mensaje: "Cada marca roja es un punto donde hoy hay trabajo manual."

**4. Dimensión.** Decir "estimaciones de la organización" con esas palabras. "Las confirmamos con la organización pero no las medimos nosotros: por eso proponemos un piloto."

**5. Propuesta.** Mostrar los dos diagramas lado a lado. "Mismos actores, mismas etapas. Lo verde es lo que hace el sistema. La línea punteada es un aviso nuevo: el socio se entera de su remito sin llamar."

**6. Qué cambia.** Cerrar con la idea de que se mantienen la negociación y el control físico, que son tareas de criterio humano.

**7. Prototipo.** Pasar el video mudo y narrar con el guion de `guion_video.md`. Si falla el video, mostrar las 6 etapas de la diapositiva y ofrecer abrir el programa al final.

**8. Por qué conviene.** Decir con claridad qué es meta y qué es estimación. No afirmar un plazo de recupero de la inversión ni plazos o costos de implementación: el grupo no los calculó.

**9. Cómo se llega a producción.** Pasar rápido por las etapas y detenerse en los riesgos que la dirección puede preguntar: usuarios simultáneos, SAP y datos reales.

**10. Pedido de decisión.** Pedir una sola cosa y dejar la diapositiva a la vista durante las preguntas.

## Preguntas probables y respuestas

- **¿Cuánto cuesta?** El prototipo no usa licencias de terceros y corre sobre la infraestructura existente. El costo de implementación todavía no está calculado: no dar una cifra.
- **¿Cuánto tarda en estar en producción?** Todavía no calculamos plazos. El primer paso es el piloto con dos socios, y de sus resultados depende el cronograma de la integración con IT.
- **¿Son reales esas cifras de horas y papel?** Son estimaciones del relevamiento. El piloto con dos socios las convierte en mediciones.
- **¿Qué pasa si el proveedor entrega menos de lo pedido?** El sistema reparte con una sola regla proporcional, igual para todos los socios, y le pide confirmación al ejecutivo antes de emitir los remitos.
- **¿Se integra con SAP y con el sistema actual?** Todavía no. Es la etapa de integración con IT, que mantiene el sistema de gestión desde hace 30 años y sería quien lo integre.
- **¿Es seguro?** El prototipo usa credenciales de prueba y no debe usarse con datos reales. El cifrado y el manejo de secretos se resuelven en la integración.
- **¿Logística tiene su propio usuario?** Hoy no: la recepción la registra un usuario ejecutivo o administrador. Está identificado como mejora (limitación L-04).

---

# PARTE C: PENDIENTES

**Resueltos**
- No se calcularon duraciones ni costos de implementación: ninguna diapositiva los incluye.
- La corrección de L-01 no se aclara en la exposición.
- "Sin licencias de terceros" se dice solo "en el prototipo", por la licencia de PyQt6.
- La portada (integrantes y materia) la completa Sergio.

**Pendientes con el grupo**
1. **Datos de prueba.** Los socios de prueba tienen nombres gastronómicos y el caso real son 12 supermercadistas. En el video conviene aclarar que son datos de prueba (la diapositiva 7 ya lo dice).
2. **Cuarto criterio de éxito del documento 06** (cero artículos sin repartir por pedidos con varios proveedores). Quedó fuera de la diapositiva 10.
3. **Quién graba el video** y el ensayo del recorrido con la base reseteada.
4. **Cifras de plazo del documento 06.** El 06 habla de un plan de 6 semanas y de unas 3 semanas de integración con IT, y nombra una etapa E7. Las diapositivas no los usan porque el grupo no calculó duraciones. Si el grupo respalda esas cifras, se agregan a las diapositivas 8 y 9.
