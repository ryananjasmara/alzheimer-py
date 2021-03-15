# import necessary packages
import flask
import hashlib
from flask import Flask, render_template, request, json, redirect, session, url_for
from flaskext.mysql import MySQL

# create the flask app
app = Flask(__name__)
app.secret_key = 'alzheimerflaskbescret'
mysql = MySQL()

# Other configurations
app.config['JSON_SORT_KEYS'] = False

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'db_alzheimer'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# MD5 encryption
def computeMD5hash(my_string):
    m = hashlib.md5()
    m.update(my_string.encode('utf-8'))
    return m.hexdigest()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # data
        email = request.form['email']
        password = request.form['password']
        # check if login as admin / dokter
        if email == 'admin@alz.com' and password == 'alz2021':
            session['logined'] = True
            session['login_as'] = 'admin'
            session['nama'] = 'Admin'
            return redirect('/home')
        else:
            # fetch
            conn = mysql.connect()
            cursor = conn.cursor()
            query = "SELECT * FROM tbl_dokter WHERE email_dokter=%s AND password_dokter=md5(%s)"
            param = (email, password)
            cursor.execute(query, param)
            columns = cursor.description
            result = [{columns[index][0]:column for index,column in enumerate(value)} for value in cursor.fetchall()]
            if len(result) > 0:
                session['logined'] = True
                session['login_as'] = 'dokter'
                session['id'] = result[0]['id_dokter']
                session['nama'] = result[0]['nama_dokter']
                session['email'] = result[0]['email_dokter']
                
                return redirect('/home')
            else:
                messages = "username atau password anda tidak sesuai"
                return flask.render_template('login.html', error=messages)
    else:
        return flask.render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # data
        nama = request.form['nama']
        email = request.form['email']
        password = computeMD5hash(request.form['password'])
        confirm_password = computeMD5hash(request.form['confirm_password'])
        if password != confirm_password:
            messages = "password dan konfirmasi password tidak sesuai"
            return flask.render_template('register.html', error=messages)
        # fetch
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "INSERT INTO tbl_dokter (nama_dokter, email_dokter, password_dokter) values (%s, %s, %s)"
        param = (nama, email, password)
        try:
            cursor.execute(query, param)
            conn.commit()
            return redirect('/')
        except Exception as e:
            messages = "terjadi kesalahan sehingga registrasi gagal, silahkan coba lagi"
            return flask.render_template('register.html', error=messages)
    else:
        return flask.render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/') 


@app.route('/home')
def home():
    is_login = session.get('logined')
    login_as = session.get('login_as')
    if is_login == True:
        session['page'] = 'home'
        # fetch
        conn = mysql.connect()
        cursor = conn.cursor()
        if login_as == 'admin':
            # pasien
            query = "SELECT count(id_pasien) as count FROM tbl_pasien"
            cursor.execute(query)
            columns = cursor.description
            result = [{columns[index][0]:column for index,column in enumerate(value)} for value in cursor.fetchall()]
            count_pasien = result[0]['count']
            # dokter
            query = "SELECT count(id_dokter) as count FROM tbl_dokter"
            cursor.execute(query)
            columns = cursor.description
            result = [{columns[index][0]:column for index,column in enumerate(value)} for value in cursor.fetchall()]
            count_dokter = result[0]['count']
            return flask.render_template('home.html', count_pasien=count_pasien, count_dokter=count_dokter)
        else:
            return flask.render_template('home.html')
    else:
        return redirect('/')


@app.route('/dokter')
def dokter():
    is_login = session.get('logined')
    if is_login == True:
        session['page'] = 'dokter'
        # fetch
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM tbl_dokter"
        cursor.execute(query)
        columns = cursor.description
        result = [{columns[index][0]:column for index,column in enumerate(value)} for value in cursor.fetchall()]
        return flask.render_template('dokter_list.html', data=result)
    else:
        return redirect('/')

@app.route('/hapus_dokter/<id_dokter>')
def hapus_dokter(id_dokter):
    # fetch
    conn = mysql.connect()
    cursor = conn.cursor()
    query = "DELETE FROM tbl_dokter WHERE id_dokter=%s"
    param = (id_dokter)
    cursor.execute(query, param)
    conn.commit()
    return redirect('/dokter')


@app.route('/edit_dokter/<id_dokter>', methods=['POST'])
def edit_dokter(id_dokter):
    # data
    nama = request.form['nama']
    email = request.form['email']
    password = request.form['password']
    # fetch
    conn = mysql.connect()
    cursor = conn.cursor()
    if password != '':
        query = "UPDATE tbl_dokter SET nama_dokter=%s, email_dokter=%s, password_dokter=md5(%s) WHERE id_dokter=%s"
        param = (nama, email, password, id_dokter)
        cursor.execute(query, param)
        conn.commit()
    else:
        query = "UPDATE tbl_dokter SET nama_dokter=%s, email_dokter=%s WHERE id_dokter=%s"
        param = (nama, email, id_dokter)
        cursor.execute(query, param)
        conn.commit()
    return redirect('/dokter')


@app.route('/pasien')
def pasien():
    is_login = session.get('logined')
    if is_login == True:
        session['page'] = 'pasien'
        # fetch
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM tbl_pasien"
        cursor.execute(query)
        columns = cursor.description
        result = [{columns[index][0]:column for index,column in enumerate(value)} for value in cursor.fetchall()]
        return flask.render_template('pasien_list.html', data=result)
    else:
        return redirect('/')


@app.route('/hapus_pasien/<id_pasien>')
def hapus_pasien(id_pasien):
    # fetch
    conn = mysql.connect()
    cursor = conn.cursor()
    query = "DELETE FROM tbl_pasien WHERE id_pasien=%s"
    param = (id_pasien)
    cursor.execute(query, param)
    conn.commit()
    return redirect('/pasien')


@app.route('/edit_pasien/<id_pasien>', methods=['POST'])
def edit_pasien(id_pasien):
    # data
    nama = request.form['nama']
    kontak = request.form['kontak']
    tanggal_lahir = request.form['tanggal_lahir']
    jenis_kelamin = request.form['jenis_kelamin']
    alamat = request.form['alamat']
    # fetch
    conn = mysql.connect()
    cursor = conn.cursor()
    query = "UPDATE tbl_pasien SET nama_pasien=%s, kontak_pasien=%s, tanggal_lahir_pasien=%s, jenis_kelamin_pasien=%s, alamat_pasien=%s WHERE id_pasien=%s"
    param = (nama, kontak, tanggal_lahir, jenis_kelamin, alamat, id_pasien)
    cursor.execute(query, param)
    conn.commit()
    return redirect('/pasien')


@app.route('/tambah_pasien', methods=['POST'])
def tambah_pasien():
    # data
    nama = request.form['nama']
    kontak = request.form['kontak']
    tanggal_lahir = request.form['tanggal_lahir']
    jenis_kelamin = request.form['jenis_kelamin']
    alamat = request.form['alamat']
    # fetch
    conn = mysql.connect()
    cursor = conn.cursor()
    query = "INSERT INTO tbl_pasien (nama_pasien, kontak_pasien, tanggal_lahir_pasien, jenis_kelamin_pasien, alamat_pasien) values (%s, %s, %s, %s, %s)"
    param = (nama, kontak, tanggal_lahir, jenis_kelamin, alamat)
    cursor.execute(query, param)
    conn.commit()
    return redirect('/pasien')

# run the app
app.run()
