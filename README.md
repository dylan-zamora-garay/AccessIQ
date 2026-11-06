AccessIQ
Sistema de control de acceso inteligente con reconocimiento facial
AccessIQ es una aplicación web que permite a pequeños negocios y oficinas decidir, de forma automática y en tiempo real, quién puede entrar a sus instalaciones. En lugar de llaves, tarjetas o cuadernos de registro, la persona simplemente se para frente a una cámara: el sistema reconoce su rostro, revisa si tiene permiso y si está dentro de su horario, y le responde al instante con un "acceso autorizado" o un "acceso denegado". Cada intento queda guardado para que el administrador pueda consultarlo cuando quiera.
Pruébalo en línea: https://dylanzamora07205.pythonanywhere.com
---
¿Por qué creamos AccessIQ?
En muchos negocios pequeños el control de entrada se hace a mano: alguien abre la puerta, se anota en un cuaderno o se reparten llaves que luego nadie sabe quién tiene. Esto trae problemas muy comunes:
No hay certeza de quién entró ni a qué hora.
Las llaves y tarjetas se pierden, se prestan o se copian.
Es difícil limitar el acceso a ciertos horarios (por ejemplo, que un empleado solo entre en su turno).
Revisar el historial de entradas toma tiempo y suele estar incompleto.
AccessIQ resuelve estos problemas con una herramienta sencilla de usar, que no requiere comprar equipos costosos: basta con un computador y una cámara.
---
¿Cómo funciona?
El funcionamiento es simple y se resume en cuatro pasos:
Se registra a la persona. El administrador guarda su nombre, su número de identificación, una foto de su rostro, el horario en el que puede entrar y si tiene el acceso autorizado o denegado.
La persona llega y se para frente a la cámara. Esto se hace desde la pantalla de Entrada.
El sistema compara el rostro con las fotos de las personas registradas y revisa tres cosas: que la persona exista en el sistema, que tenga permiso y que la hora actual esté dentro de su horario.
El sistema responde y lo registra. Muestra el resultado en pantalla (verde si puede entrar, rojo si no), lo dice en voz alta y guarda el intento con la fecha, la hora y el motivo.
¿Cuándo se rechaza un acceso?
El sistema niega la entrada en tres casos, y siempre explica por qué:
Rostro no registrado: la persona no está en el sistema.
Permiso denegado: la persona está registrada, pero el administrador le quitó el acceso.
Fuera de horario: la persona tiene permiso, pero intenta entrar en una hora que no le corresponde.
Cuando el rostro es desconocido, el sistema además guarda una pequeña imagen de ese intento. Así, el administrador puede ver quién fue y no se queda solo con un signo de interrogación.
---
Las pantallas del sistema
Inicio. La página de bienvenida, con el nombre del sistema y el botón para iniciar sesión.
Iniciar sesión. Cada persona que administra el sistema entra con su propio usuario y contraseña.
Panel. El resumen general: cuántas personas están registradas, cuántos accesos se autorizaron hoy, cuántos intentos se rechazaron y una lista con la actividad más reciente, con las fotos de quienes pasaron por la cámara.
Personas. Aquí se registran, editan y eliminan las personas que pueden usar el sistema. La foto se puede tomar directamente con la cámara o subir desde el computador. Si el horario o el permiso de alguien cambia, se edita sin necesidad de volver a registrarlo.
Entrada. La pantalla que ve la persona que quiere ingresar. Muestra la cámara, el botón para verificar y el resultado. Además, el sistema lee el resultado en voz alta (por ejemplo: "Acceso autorizado. Hola, Laura"), y esa voz se puede silenciar con un botón.
Historial. El registro completo de todos los intentos de acceso. Se puede buscar por nombre o identificación, filtrar por resultado (autorizados o rechazados) y por fechas, y descargar la información en un archivo que se abre en Excel, útil para reportes o revisiones.
Usuarios. Disponible solo para el administrador. Desde aquí se crean las cuentas de las demás personas que usarán el sistema, se les cambia la contraseña o se eliminan.
---
Usuarios y permisos del sistema
AccessIQ distingue dos tipos de cuenta:
Administrador: puede hacer todo, incluida la gestión de usuarios. Es el único que ve la pestaña Usuarios.
Usuario: puede usar el resto del sistema (panel, personas, entrada e historial), pero no puede crear ni eliminar cuentas.
Las contraseñas se guardan cifradas, de modo que ni siquiera quien administra la base de datos puede leerlas. Si una cuenta se elimina, esa persona pierde el acceso de inmediato.
---
Guía rápida de uso
Para el administrador, la primera vez:
Entra a la dirección del sistema e inicia sesión con la cuenta de administrador.
Entra a Usuarios y cambia la contraseña inicial por una propia.
Crea una cuenta para cada persona que vaya a usar el sistema.
Entra a Personas y registra a quienes tendrán acceso, con una foto de frente y con buena luz.
Para el uso diario:
Abre la pantalla de Entrada y permite el uso de la cámara cuando el navegador lo pida.
La persona se para frente a la cámara, mirando de frente.
Se presiona Verificar acceso y el sistema responde.
Cuando se quiera revisar lo ocurrido, se consulta el Historial o la actividad reciente del Panel.
Consejos para que el reconocimiento funcione mejor: usar fotos de frente, con buena iluminación y con un solo rostro visible, tanto al registrar a la persona como al verificarla.
---
¿Con qué está hecho?
Para quien tenga curiosidad, sin entrar en detalles:
Python y Flask: el "cerebro" del sistema y la forma en que se muestra como página web.
Una base de datos sencilla (SQLite): donde se guardan las personas, los usuarios y el historial.
Una librería de reconocimiento facial: la encargada de comparar los rostros.
HTML, CSS y JavaScript: el diseño de las pantallas, en tonos naranja y negro, y el uso de la cámara y de la voz desde el navegador.
PythonAnywhere: el servicio donde el sistema está publicado para poder usarlo desde internet.
Todo el sistema trabaja con la hora de Colombia, sin importar la hora que tenga configurada el computador o el servidor.
---
Dónde está publicado
AccessIQ ya está en línea y se puede usar desde cualquier computador con internet, sin instalar nada:
https://dylanzamora07205.pythonanywhere.com
Al entrar aparece la página de bienvenida. Desde ahí se presiona Iniciar sesión y se ingresa con el usuario y la contraseña que haya creado el administrador. Cuando el navegador lo pida, hay que permitir el uso de la cámara; funciona porque la dirección es segura (https).
---
Instalación en un computador (opcional)
Como el sistema ya está publicado, esta sección solo es necesaria para quien quiera correr su propia copia.
Instalar Python 3.10 (o una versión compatible).
Instalar las librerías necesarias abriendo una terminal y escribiendo, una por una:
```
   pip install flask
   pip install dlib-bin
   pip install face\_recognition --no-deps
   pip install face\_recognition\_models Click Pillow numpy opencv-python
   ```
Guardar todos los archivos del proyecto en una misma carpeta: `app.py`, `inicio.html`, `login.html`, `panel.html`, `personas.html`, `entrada.html`, `historial.html` y `usuarios.html`.
Ejecutar el programa con `python app.py`.
Abrir en el navegador la dirección `http://127.0.0.1:5000`.
La base de datos y las carpetas para las fotos se crean solas la primera vez que se ejecuta. En ese primer arranque se crea también la cuenta de administrador inicial: recuerda cambiar su contraseña desde la pestaña Usuarios.
---
Cuidado con los datos personales
Un sistema de reconocimiento facial maneja información delicada, como las fotos del rostro de las personas. Por eso recomendamos:
Usarlo únicamente con personas que hayan dado su permiso para ser registradas.
Cambiar las contraseñas iniciales y mantener en privado las cuentas de administrador.
Eliminar del sistema a quienes ya no necesiten acceso.
Revisar de vez en cuando las imágenes guardadas de los intentos rechazados y borrarlas si ya no se necesitan.
---
Limitaciones actuales
AccessIQ es un prototipo desarrollado como proyecto de clase, y por eso tiene algunas limitaciones que conviene conocer:
El reconocimiento puede fallar con poca luz, con la cara de lado o con la cámara muy lejos.
Todavía no está conectado a una puerta o cerradura real: el sistema decide si se puede entrar, pero no abre nada físicamente.
No debe usarse como único sistema de seguridad en lugares donde haya riesgos graves.
Cada persona se registra con una sola foto, y para cambiarla hay que eliminarla y volver a registrarla.
---
Ideas para seguir mejorándolo
Conectarlo a una cerradura o a una puerta real, por ejemplo con un pequeño motor que simule su apertura.
Permitir que cada usuario cambie su propia contraseña.
Poder cambiar la foto de una persona sin tener que volver a registrarla.
Limpiar automáticamente las imágenes antiguas de intentos rechazados.
Agregar gráficas y reportes, como las horas de más movimiento o las personas que más entran.
Enviar avisos al administrador cuando haya varios intentos rechazados seguidos.
---
El equipo y la forma de trabajo
AccessIQ fue desarrollado por un equipo de cuatro personas, usando la metodología Scrum, que consiste en avanzar por etapas cortas llamadas sprints, revisando y mejorando el trabajo al final de cada una. Se realizaron aproximadamente 10 sprints y cerca de 5 entrevistas con posibles usuarios, cuyas opiniones ayudaron a decidir qué funciones debía tener el sistema.
Rol	Integrante
Scrum Master	Dylan Alexander Zamora
Product Owner	Ana Maria Wilches
Developer	Deyvi Samuel Rojas
Developer	Juan

Institución: Universidad Cooperativa de Colombia
Fecha: Noviembre - 2026
---
AccessIQ: acceso seguro, de forma simple.
