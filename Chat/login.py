from flask import Flask, flash, redirect, render_template, request, session,abort,g
import os,psycopg2,psycopg2.extras,sys,time,datetime,ipgetter,requests


app = Flask(__name__)
app.static_folder = 'static'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def home():
#si vuelve a caer en home y existe la session da la opcion de salir
     if not session.get('logged_in'):
        return render_template('login.html')
     else:
        return "<a href='/logout'>Salir!</a>"

@app.route('/reg')
#si trata de registrarse teniendo una session abierta, da la opcion de salir
def register():
    if not session.get('logged_in'):
        return render_template('register.html')
    else:
       return "<a href='/logout'>Salir!</a>"


@app.route('/subir', methods = ['GET', 'POST'])
def subir():
    #Esta funcion permite subir archivos al filesystem de la aplicacion, crea una carpeta con el id de la relacion y ahi mete los archivos
    #Adicional guarda en la base de datos en la tabla archivos la ruta y el nombre del archivo
    #al nombre del archivo se le adiciona a la extension time.time() para evitar de que si se repiten nombres no sean reemplazados
    #finalmente regresa al chat
    try:
        if request.method == 'POST':
            id_usuario_a = session['id_usuario_a']
            id_usuario_b = session['id_usuario_b']
            id_relacion = session['id_relacion']
            if not os.path.exists('static/'+id_relacion):
                os.mkdir('static/'+id_relacion)
            f = request.files['file']
            hora=time.time()
            archivo1='static/'+id_relacion+'/'+f.filename
            archivo2=str(f.filename)+'.'+str(hora)
            print('El archivo es ', archivo1,archivo2)
            f.save(archivo1)
            os.rename(archivo1,archivo1+'.'+str(hora))
            id_usuario_a = session['id_usuario_a']
            id_usuario_b = session['id_usuario_b']
            id_relacion = session['id_relacion']
            print("imprimiendo ",id_relacion, f.filename,id_usuario_a,id_usuario_b)
            #Genera la conexion a postgres, se hace el insert a la base de datos a la tabla archivo , se inserta usuando el id_relacion
            conn_string = "host='localhost' dbname='chat' user='postgres' password='aftro1064'"
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            conn.autocommit = True
            SQL = "INSERT INTO chat.archivo (id_relacion,path,nombre) VALUES (%s,%s,%s)"
            cursor.execute(SQL,(id_relacion,id_relacion, archivo2))
            conn.close()
            return en_linea(session['id_usuario_a'], session['id_usuario_b'])
        else:
            return en_linea(session['id_usuario_a'], session['id_usuario_b'])
    except:
        conn.close()
        return en_linea(session['id_usuario_a'], session['id_usuario_b'])





#Funcion login

@app.route('/login', methods=['POST'])
def admon_login():
    #Usando el servicio de freegeoip.net retorna usando json la ubicacion de la ip publica
    #Login a la aplicacion, se introduce email, contrasena y esta es comparada si existe en la base de datos de postgres . tabla usuario
    #Si existe la cuenta, se crea una session para ser usada a lo largo de la aplicacion
    #Se hace un update a la base de datos sobre el campo enlinea(de offline a online)
    #Una ves autenticado pasa a la funcion en_linea que es la sala del chat

    try:
        IP = ipgetter.myip()
        url = 'http://freegeoip.net/json/' + IP
        r = requests.get(url)
        js = r.json()

        #print('IP Adress: ' + js['ip'])
        #print('Country Code: ' + js['country_code'])
        #print('Country Name: ' + js['country_name'])
        #print('Region Code: ' + js['region_code'])
        #print('Region Name: ' + js['region_name'])
        #print('City Name: ' + js['city'])
        #print('Zip code: ' + js['zip_code'])
        #print('Time Zone: ' + js['time_zone'])
        #print('Latitude: ' + str(js['latitude']))
        #print('Longitude: ' + str(js['longitude']))

        _username = request.form['username']
        _password = request.form['password']
        conn_string = "host='localhost' dbname='chat' user='postgres' password='aftro1064'"
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor1 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        SQL="SELECT id_usuario,correo,clave,enlinea,nombre FROM chat.usuario where correo='" + _username+ "'"
        cursor.execute(SQL)
        records = cursor.fetchone()
        session.pop('user',None)
        if _password == records['clave'] and _username == records['correo']:
            session['logged_in'] = True
            session['user']=_username
            session['id_usuario_a']=records['id_usuario']
            session['enlinea']=records['enlinea']
            session['nombre']=records['nombre']
            session['geo']=js['country_code']
            SQL1 = "UPDATE chat.usuario SET enlinea = 'online' WHERE id_usuario ="+str(records['id_usuario'])
            print(SQL1)
            cursor1.execute(SQL1)
            conn.close()
            return en_linea(records['id_usuario'],0)
        else:
            flash('usuario o clave erradas!')
            return home()
    except:
        print("usuario o clave erradas!")
    return home()



@app.route('/mensaje', methods=['POST'])
def mensaje():
    #Esta funcion inserta un mensaje dentro de postgres en la tabla mensaje
    #La inserccion usa id_relacion, para poner el mensaje relacionado entre dos personas
    #A cada mensaje se le pone nombre, mensaje, fecha , hora y la georeferenciacion de la ip
    try:
        _mensaje = request.form['mensaje']
        if  _mensaje!="":
            print("EL MENSAJE ES ",_mensaje)
            print(session['id_usuario_a'])
            print(session['id_usuario_b'])
            print(session['id_relacion'])
            id_usuario_a=session['id_usuario_a']
            id_usuario_b=session['id_usuario_b']
            id_relacion=session['id_relacion']
            fechahora = datetime.datetime.now().strftime("(%Y-%m-%d) %H:%M")
            MSG=session['nombre'] + ' : '+ _mensaje +"    "+ fechahora + ' '+ session['geo']
            print(MSG)
            conn_string = "host='localhost' dbname='chat' user='postgres' password='aftro1064'"
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            conn.autocommit = True
            SQL = "INSERT INTO chat.mensaje (id_relacion,mensaje) VALUES (%s,%s)"
            cursor.execute(SQL,(id_relacion,MSG))
            conn.close()
            return en_linea(session['id_usuario_a'], session['id_usuario_b'])
        else:
            return en_linea(session['id_usuario_a'],session['id_usuario_b'])
    except:
        conn.close()
        return en_linea(session['id_usuario_a'], session['id_usuario_b'])





@app.route('/solicitud', methods=['POST'])
def solicitud():
    #Esta funcion inserta en la tabla invitacion el correo de quien esta solicitando y al solicitante
    #Esta tabla no contiene llaves contra las otras tablas, esto es para permitir que se envie una solicitud a alguien que aun no se ha registrado
    try:
        _correo = request.form['correo']
        if  _correo!="":
            print("EL MENSAJE ES ",_correo)
            print(session['user'])
            correo_a=session['user']
            conn_string = "host='localhost' dbname='chat' user='postgres' password='aftro1064'"
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            conn.autocommit = True
            SQL = "INSERT INTO chat.invitacion (correo_solicitud,correo_solicitante) VALUES (%s,%s)"
            cursor.execute(SQL,(correo_a,_correo))
            conn.close()
            return en_linea(session['id_usuario_a'], session['id_usuario_b'])
        else:
            return en_linea(session['id_usuario_a'],session['id_usuario_b'])
    except:
        conn.close()
        return en_linea(session['id_usuario_a'], session['id_usuario_b'])

#Funcion de Registro

@app.route('/register', methods=['POST'])
def admon_register():
    #Permite Registrar dentro de la aplicacion un usuario, se pide nombre , correo y clave
    try:
        _name = request.form['name']
        _password=request.form['password']
        _username=request.form['username']
        conn_string = "host='localhost' dbname='chat' user='postgres' password='aftro1064'"
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        SQL="INSERT INTO chat.usuario (nombre,correo,clave) VALUES('" +_name + "','" + _username + "','" + _password + "')"
        print(SQL)
        cursor.execute(SQL)
        print("Usuario ya existe con ese correo")
        conn.close()
        return home()
    except:
        print("usuario existe!")
        conn.close()
        return home()

@app.route("/logout")
def logout():
    #Permite cerrar la session y la variable logged_in pasarla a False
    # Se hace un update a la base de datos sobre el campo enlinea(de online a offline)
    conn_string = "host='localhost' dbname='chat' user='postgres' password='aftro1064'"
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor1 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    SQL1 = "UPDATE chat.usuario SET enlinea = 'offline' WHERE id_usuario =" + str(session['id_usuario_a'])
    print(SQL1)
    cursor1.execute(SQL1)
    conn.close()
    session['logged_in'] = False
    return home()

#Funcion Relacion, relaciona la conversacion entre dos personas

@app.route('/relacion/<id_usuario_b>&<correo_b>')
def relacion(id_usuario_b,correo_b):
    try:
        #Esta funcion relaciona dos personas para establecer una comunicacion en el chat
        #Inserta un registro en la tabla relacion usando id_usuario_a y id_usuario_b
        #Con el id_relacion puedo relacionar mensajes y archivos
        #El tramite de la relacion se hace a partir de una solicitud, una ves se lee esta solicitud y se comparan los correos
        #de la solicitud , con el login actual del usuario , se inserta la relacion y se borra el registro de la tabla invitacion
        id_usuario_a=session['id_usuario_a']
        user = session['user']
        conn_string = "host='localhost' dbname='chat' user='postgres' password='aftro1064'"
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor2 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor3 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        CHK1='SELECT chat.relacion.id_usuario_a, chat.relacion.id_usuario_b FROM chat.relacion WHERE '\
             '(chat.relacion.id_usuario_a='+ str(id_usuario_a) + \
             ' AND '\
             'chat.relacion.id_usuario_b='+ str(id_usuario_b) +')'\
             ' OR ' \
             '(chat.relacion.id_usuario_b='+ str(id_usuario_a) + \
             ' AND chat.relacion.id_usuario_a=' + str(id_usuario_b) + ')'
        SQL1 = 'INSERT INTO chat.relacion(id_usuario_a, id_usuario_b) VALUES(%s, %s)'
        SQL2 = 'DELETE FROM chat.invitacion WHERE correo_solicitud=%s and correo_solicitante=%s'

        #La insercion se hace solo si no existe ya una relacion creada y el usuario_a es diferente al usuario_b
        cursor3.execute(CHK1, (id_usuario_a, id_usuario_b,))
        if cursor3.rowcount==0 and int(id_usuario_b)!=int(id_usuario_a):
            cursor1 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor1.execute(SQL1, (id_usuario_a, id_usuario_b))
            cursor2.execute(SQL2, (correo_b, user))
            return en_linea(session['id_usuario_a'], session['id_usuario_b'])
            conn.close()
        else:
            cursor2.execute(SQL2, (correo_b, user))
            conn.close()
        return en_linea(session['id_usuario_a'], session['id_usuario_b'])
    except:
        cursor2.execute(SQL2, (correo_b, user))
        conn.close()
        return en_linea(session['id_usuario_a'], session['id_usuario_b'])








@app.route('/enlinea/<id_usuario_a>&<id_usuario_b>')
def en_linea(id_usuario_a,id_usuario_b):
            try:
                #Esta funcion es la sala del chat, aqui se pinta en el template
                #La relacion de contactos de acuerdo a la session
                #Muesta los mensajes relacionados y los archivos relacionados
                #Muestra la lista de solicitudes
                session['id_usuario_b']=id_usuario_b
                conn_string = "host='localhost' dbname='chat' user='postgres' password='aftro1064'"
                conn = psycopg2.connect(conn_string)
                conn.autocommit = True
                cursor1 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor2 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor3 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor4 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor5 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                session['id_usuario']=id_usuario_a

                SQL1 =  'SELECT ' \
                        'chat.ralacion_v.id_relacion,  ' \
                        'chat.ralacion_v.correo_a,  ' \
                        'chat.ralacion_v.id_usuario_a, '\
                        'chat.ralacion_v.id_usuario_b, '\
                        'chat.ralacion_v.nombre_b, ' \
                        'chat.ralacion_v.enlinea '\
                        'FROM '\
                        'chat.ralacion_v '\
                        'WHERE '\
                        'chat.ralacion_v.id_usuario_a ='+str(id_usuario_a)

                SQL2 = 'SELECT ' \
                       'chat.mensajes_v.id_usuario_a, ' \
                       'chat.mensajes_v.id_usuario_b, ' \
                       'chat.mensajes_v.id_mensaje, ' \
                       'chat.mensajes_v.mensaje ' \
                       'FROM ' \
                       'chat.mensajes_v ' \
                       'WHERE ' \
                       'chat.mensajes_v.id_usuario_a ='+str(id_usuario_a) +\
                       ' and ' \
                       'chat.mensajes_v.id_usuario_b ='+str(id_usuario_b) +\
                       'ORDER BY chat.mensajes_v.id_mensaje ASC'

                SQL3 = 'SELECT ' \
                       'chat.ralacion_v.id_relacion  ' \
                       'FROM ' \
                       'chat.ralacion_v ' \
                       'WHERE ' \
                       'chat.ralacion_v.id_usuario_a ='+str(id_usuario_a) +\
                       ' and ' \
                       'chat.ralacion_v.id_usuario_b ='+str(id_usuario_b)

                SQL4 =  'SELECT '\
                        'chat.invitacion_v.correo_solicitud, '\
                        'chat.invitacion_v.correo_solicitante, '\
                        'chat.invitacion_v.correo '\
                        'FROM '\
                        'chat.invitacion_v '\
                        'WHERE '\
                        'chat.invitacion_v.correo_solicitante = '+str(id_usuario_a)

                SQL5=   'SELECT '\
                        'chat.archivos_v.id_usuario_b, '\
                        'chat.archivos_v.id_usuario_a, '\
                        'archivos_v.path, '\
                        'chat.archivos_v.nombre '\
                        'FROM '\
                        'chat.archivos_v '\
                        'WHERE '\
                        'archivos_v.id_usuario_a='+str(id_usuario_a) +\
                        'AND '\
                        'archivos_v.id_usuario_b='+str(id_usuario_b) +\
                        'ORDER BY chat.archivos_v.id_archivo ASC'


                cursor1.execute(SQL1)
                cursor2.execute(SQL2)
                cursor3.execute(SQL3)
                cursor4.execute(SQL4)
                cursor5.execute(SQL5)

                print(SQL5)
            except:
                print("vacio el query")
            records1 = cursor1.fetchall()
            records2 = cursor2.fetchall()
            records3 = cursor3.fetchone()
            records4 = cursor4.fetchall()
            records5 = cursor5.fetchall()

            print(records1)
            print(records2)
            print(records3)
            print(records4)
            print(records5)
            conn.close()
            if records3:
                session['id_relacion']=str(records3['id_relacion'])
            return render_template('chat.html', usuarios=records1,mensajes=records2,solicitudes=records4,archivos=records5)



if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(host='192.168.1.106', port=5000)
    app.run(debug=True)
    #app.config['TEMPLATES_AUTO_RELOAD'] = True

