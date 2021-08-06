from flask import Flask
from flask import render_template, request, redirect, flash, url_for
from flaskext.mysql import MySQL
from sklearn.cluster import KMeans
import numpy as np
from sklearn.decomposition import PCA
import csv
from sklearn import preprocessing
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "Development"

mysql= MySQL()
app.config['MYSQL_DATABASE_HOST']='db4free.net'
app.config['MYSQL_DATABASE_PORT']=3306
app.config['MYSQL_DATABASE_USER']='luischo'
app.config['MYSQL_DATABASE_PASSWORD']='123456Lf*'
app.config['MYSQL_DATABASE_DB']='zodiaco'
mysql.init_app(app)

@app.route('/importar')
def importar():
    return render_template('horoscopo/importar.html')

@app.route('/storeCSV', methods=['POST'])
def storeCSV():
    _file = request.files['fileCSV']
    if _file.filename == '':
        flash("Seleccione un archivo")
        return redirect(url_for('importar'))
    else:
        _file.save("files/"+_file.filename)
        flash("Archivo guardado")
        return render_template('horoscopo/importar.html', nombre_file=_file.filename)

@app.route('/kmeans/<int:id>')
def kmeans(id):
    #Obtener datos de BD
    sql = "SELECT id, caracteristica_1, caracteristica_2, caracteristica_3, caracteristica_3, caracteristica_5, caracteristica_6, caracteristica_7, caracteristica_8 FROM `usuario`;"
    conn= mysql.connect()
    cursor=conn.cursor()
    cursor.execute(sql)
    result=cursor.fetchall()
    conn.commit()
    headers = ['id', 'caracteristica_1', 'caracteristica_2', 'caracteristica_3', 'caracteristica_4', 'caracteristica_5', 'caracteristica_6', 'caracteristica_7', 'caracteristica_8']
    with open("kmeans_algoritmo.csv", "w", newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(i for i in headers)
        for row in result:
            writer.writerow(row)
    #Cargar datos
    data = pd.read_csv("kmeans_algoritmo.csv", engine='python')
    #data = pd.read_csv("wholesale customers data.csv", engine='python')
    #Analizar datos
    data.shape
    #Conocer datos nulos
    data.isnull().sum()
    #Conocer el formato de datos
    data.dtypes
    #Seleccionar datos al azar
    indices = [id-1]
    muestras = pd.DataFrame(data.loc[indices], columns=data.keys()).reset_index(drop = True)
    data = data.drop(indices, axis=0)
    #Procesamiento de datos
    data = data.drop(['id'], axis=1)
    muestras = muestras.drop(['id'], axis=1)
    #Reescalar datos
    X = data.copy()
    ###  Valor optimo 12, por los horoscopos  ###
    #Algorimto de clustering
    algoritmo = KMeans(n_clusters = 12, init = 'k-means++',
                        max_iter = 300, n_init = 10)
    algoritmo.fit(X)
    centroides, etiquetas = algoritmo.cluster_centers_, algoritmo.labels_
    #Graficar datos
    modelo_pca = PCA(n_components = 2)
    modelo_pca.fit(X)
    pca = modelo_pca.transform(X)
    #Aplicar reduccion dimensionalidad a centroides
    centroides_pca = modelo_pca.transform(centroides)
    #Colores de clusters
    colores = ["blue", "green", "orange", "red", "silver", "pink", "purple", "yellow", "aqua", "gray", "brown", "bisque"]
    #Asignar color a cluster
    colores_cluster = [colores[etiquetas[i]] for i in range(len(pca))]
    #Graficar PCA
    plt.scatter(pca[:, 0], pca[:, 1], c = colores_cluster, marker = 'o', alpha = 0.3)
    #Graficar centroides
    plt.scatter(centroides_pca[:, 0], centroides_pca[:, 1], marker = 'x', s = 100, linewidths=3, c=colores)
    #Guarda datos en variable
    xvector = modelo_pca.components_[0] * max(pca[:, 0])
    yvector = modelo_pca.components_[1] * max(pca[:, 1])
    columnas = data.columns
    #Graficar nombres de clusters
    ##for i in range(len(columnas)):
        #Graficar vectores
        ##plt.arrow(0, 0, xvector[i], yvector[i], color = 'black', width = 0.0005, head_width = 0.02, alpha = 0.75)
        #Colocar nombre
        ##plt.text(xvector[i], yvector[i], list(columnas)[i], color='black', alpha=0.75)
    plt.show()
    return redirect('/')

@app.route('/aplicarkmeans/<string:nombre_file>')
def kmeansimportar(nombre_file):
    data = pd.read_csv(nombre_file, engine='python')
    data_variable = data.drop(['Nombre'], axis=1)
    #Colocar minimo 0 y maximo 1
    data_normalizada = (data_variable-data_variable.min())/(data_variable.max()-data_variable.min())
    clustering = KMeans(n_clusters=12, max_iter=300)
    clustering.fit(data_normalizada)
    data['KMeans_Clusters'] = clustering.labels_
    pca = PCA(n_components=2)
    pca_data = pca.fit_transform(data_normalizada)
    pca_data_df = pd.DataFrame(data = pca_data, columns= ['Componente_1', 'Componente_2'])
    pca_nombres_data = pd.concat([pca_data_df, data[['KMeans_Clusters']]], axis=1)
    fig = plt.figure(figsize= (6,6))
    ax = fig.add_subplot(1,1,1)
    ax.set_xlabel('Componente 1', fontsize=15)
    ax.set_ylabel('Componente 2', fontsize=15)
    ax.set_title('Componente principales', fontsize=20)
    color_theme = np.array(["blue", "green", "orange", "red", "silver", "pink", "purple", "yellow", "aqua", "gray", "brown", "bisque"])
    ax.scatter(x = pca_nombres_data.Componente_1, y = pca_nombres_data.Componente_2, c=color_theme[pca_nombres_data.KMeans_Clusters], s=50)
    plt.show()
    return redirect('/importar')

@app.route('/')
def index():
    sql = "SELECT id, nombre, fecha_nacimiento, signo_propio, signo_compatible FROM `usuario`;"
    conn= mysql.connect()
    cursor=conn.cursor()
    cursor.execute(sql)
    data=cursor.fetchall()
    conn.commit()
    rows = len(data)
    return render_template('horoscopo/index.html', data=data, rows = rows)

@app.route('/create')
def create():
    return render_template('horoscopo/create.html')

@app.route('/store', methods=['POST'])
def storage():
    _txtNombre=request.form['txtNombre']
    _txtNacimiento=request.form['txtNacimiento']
    _txtSignoPropio=request.form['txtSignoPropio']
    _txtSignoCompatible=request.form['txtSignoCompatible']
    _txtCaracteristica1=request.form['txtCaracteristica1']
    _txtCaracteristica2=request.form['txtCaracteristica2']
    _txtCaracteristica3=request.form['txtCaracteristica3']
    _txtCaracteristica4=request.form['txtCaracteristica4']
    _txtCaracteristica5=request.form['txtCaracteristica5']
    _txtCaracteristica6=request.form['txtCaracteristica6']
    _txtCaracteristica7=request.form['txtCaracteristica7']
    _txtCaracteristica8=request.form['txtCaracteristica8']
    sql = "INSERT INTO `usuario` (`id`, `nombre`, `fecha_nacimiento`, `signo_propio`, `signo_compatible`, `caracteristica_1`, `caracteristica_2`, `caracteristica_3`, `caracteristica_4`, `caracteristica_5`, `caracteristica_6`, `caracteristica_7`, `caracteristica_8`) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
    datos=(_txtNombre, _txtNacimiento, _txtSignoPropio, _txtSignoCompatible, _txtCaracteristica1, _txtCaracteristica2, _txtCaracteristica3, _txtCaracteristica4, _txtCaracteristica5, _txtCaracteristica6, _txtCaracteristica7, _txtCaracteristica8)
    
    conn= mysql.connect()
    cursor=conn.cursor()
    cursor.execute(sql,datos)
    conn.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)