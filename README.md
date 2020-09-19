# OTICFinder

Abrir el notebook **OTICFinder.ipynb**. Clickear en el botón "Open in Colab" y seguir las instrucciones.

En la carpeta files pueden consultar el excel "direcciones_ejemplo.xlsx" con la estructura necesaria del excel. Deben coincidir el nombre exacto de las columnas. Adicionalmente, es **fuertemente recomendable** dejar vacio las casillas donde no haya información.

**Revisión de rendimiento día 16 de septiembre 2016**

Total registros analizados 472  
1. Registros vacíos = 43/472 = 9%    
2. Aciertos = 273/472 = 58% (63% eliminando registros vacios)    
3. Aciertos parciales = 23/472 = 5% (Asignados a la misma comuna pero a barrios aledaños en su mayoría - error posible en el polígono)    
4. Errores = 72/472 = 15% (Dirección proporcionada pero ubicación totalmente errada - complejidad en la información)   
5. Errores por insuficiencia 30/472 = 6% (Error causado por insuficiente información en la dirección)   
6. No encontradas = 32/472 = 7%  (Dirección muy corrupta)     

---
