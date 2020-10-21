# OTICFinder

Abrir el notebook **OTICFinder.ipynb**. Clickear en el botón "Open in Colab" y seguir las instrucciones.

**ACTUALIZACIONES EN PROCESO**: Inclusión de polígonos de municipios de santander para mayor precisión.   
**Fecha de actualización**: 25 de Octubre.  
---

En la carpeta files pueden consultar el excel "direcciones_ejemplo.xlsx" con la estructura necesaria del excel. Deben coincidir el nombre exacto de las columnas. Adicionalmente, es **fuertemente recomendable** dejar vacio las casillas donde no haya información.

**1 Revisión de rendimiento día 16 de septiembre 2020 - 16 septiembre**

Total registros analizados 472  
1. Registros vacíos o casi vacíos = 43/472 = 9%   (azules)    
2. Aciertos = 273/472 = 58% (63% eliminando registros vacíos)  (verdes)    
3. Aciertos parciales = 23/472 = 5% (Asignados a la misma comuna pero a barrios aledaños en su mayoría - error posible en el polígono) (Naranja)      
4. Errores = 72/472 = 15% (Dirección proporcionada pero ubicación totalmente errada - complejidad en la información) (rojo)         
5. Errores por insuficiencia 30/472 = 6% (Error causado por insuficiente información en la dirección)   
6. No encontradas = 32/472 = 7%  (Dirección muy corrupta)     

**2 Revisión de rendimiento día 16 de septiembre 2020 - 24 septiembre**

Total registros analizados 472  
1. Registros vacíos o casi vacíos = 52/472 = 11%   (azules)   
2. Aciertos = 281/472 = 59% (66% eliminando registros vacíos)  (verdes)    
3. Aciertos parciales = 24/472 = 5% (Asignados a la misma comuna pero a barrios aledaños en su mayoría - error posible en el polígono) (Naranja)      
4. Errores = 62/472 = 13% (Dirección proporcionada pero ubicación totalmente errada - complejidad en la información) (rojo)     
5. Errores por insuficiencia 20/472 = 4% (Error causado por insuficiente información en la dirección)   
6. No encontradas = 33/472 = 7%  (Dirección muy corrupta)  
---
