# import necessary packages
import flask
import hashlib
import math
from flask import Flask, render_template, request, json, redirect, session, url_for
from flaskext.mysql import MySQL
from sklearn import svm

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
    query = "INSERT INTO tbl_pasien (nama_pasien, kontak_pasien, tanggal_lahir_pasien, jenis_kelamin_pasien, alamat_pasien, status_pasien) values (%s, %s, %s, %s, %s, 'Belum Diagnosa')"
    param = (nama, kontak, tanggal_lahir, jenis_kelamin, alamat)
    cursor.execute(query, param)
    conn.commit()
    return redirect('/pasien')

@app.route('/diagnosa/<id_pasien>')
def diagnosa(id_pasien):
    is_login = session.get('logined')
    if is_login == True:
        session['page'] = 'pasien'
        # fetch
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM tbl_pasien WHERE id_pasien=%s"
        param = (id_pasien)
        cursor.execute(query, param)
        columns = cursor.description
        result = [{columns[index][0]:column for index,column in enumerate(value)} for value in cursor.fetchall()]
        return flask.render_template('kuesioner.html', data=result)
    else:
        return redirect('/')

@app.route('/tambah_hasil', methods=['POST'])
def tambah_hasil():
    # data
    id_pasien = request.form['id_pasien']
    # mmse
    mmse1 = int(request.form['mmse1'])
    mmse2 = int(request.form['mmse2'])
    mmse3 = int(request.form['mmse3'])
    mmse4 = int(request.form['mmse4'])
    mmse5 = int(request.form['mmse5'])
    mmse6 = int(request.form['mmse6'])
    mmse7 = int(request.form['mmse7'])
    mmse8 = int(request.form['mmse8'])
    mmse9 = int(request.form['mmse9'])
    mmse10 = int(request.form['mmse10'])
    mmse11 = int(request.form['mmse11'])
    hasil_mmse = mmse1 + mmse2 + mmse3 + mmse4 + mmse5 + mmse6 + mmse7 + mmse8 + mmse9 + mmse10 + mmse11
    # cdr 1
    cdr_1_1 = request.form['cdr-1-1']
    cdr_1_1a = request.form['cdr-1-1a']
    cdr_1_2 = request.form['cdr-1-2']
    cdr_1_3 = request.form['cdr-1-3']
    cdr_1_4 = request.form['cdr-1-4']
    cdr_1_5 = request.form['cdr-1-5']
    cdr_1_6 = request.form['cdr-1-6']
    cdr_1_7 = request.form['cdr-1-7']
    cdr_1_8 = request.form['cdr-1-8']
    cdr_1_9a = request.form['cdr-1-9a']
    cdr_1_9b = request.form['cdr-1-9b']
    cdr_1_10 = request.form['cdr-1-10']
    cdr_1_11 = request.form['cdr-1-11']
    cdr_1_12a = request.form['cdr-1-12a']
    cdr_1_12b = request.form['cdr-1-12b']
    cdr_1_12c = request.form['cdr-1-12c']
    cdr_1_12d = request.form['cdr-1-12d']
    cdr_1_13 = request.form['cdr-1-13']
    cdr_1_14 = request.form['cdr-1-14']
    cdr_1_15 = request.form['cdr-1-15']
    # cdr 2
    cdr_2_1 = request.form['cdr-2-1']
    cdr_2_2 = request.form['cdr-2-2']
    cdr_2_3 = request.form['cdr-2-3']
    cdr_2_4 = request.form['cdr-2-4']
    cdr_2_5 = request.form['cdr-2-5']
    cdr_2_6 = request.form['cdr-2-6']
    cdr_2_7 = request.form['cdr-2-7']
    cdr_2_8 = request.form['cdr-2-8']
    # cdr 3
    cdr_3_1 = request.form['cdr-3-1']
    cdr_3_2 = request.form['cdr-3-2']
    cdr_3_3 = request.form['cdr-3-3']
    cdr_3_4 = request.form['cdr-3-4']
    cdr_3_5 = request.form['cdr-3-5']
    cdr_3_6 = request.form['cdr-3-6']
    # cdr 4
    cdr_4_1 = request.form['cdr-4-1']
    cdr_4_2 = request.form['cdr-4-2']
    cdr_4_3 = request.form['cdr-4-3']
    cdr_4_4a = request.form['cdr-4-4a']
    cdr_4_4b = request.form['cdr-4-4b']
    cdr_4_5 = request.form['cdr-4-5']
    cdr_4_6 = request.form['cdr-4-6']
    cdr_4_7 = request.form['cdr-4-7']
    cdr_4_8 = request.form['cdr-4-8']
    cdr_4_9 = request.form['cdr-4-9']
    cdr_4_10 = request.form['cdr-4-10']
    # cdr 5
    cdr_5_1a = request.form['cdr-5-1a']
    cdr_5_1b = request.form['cdr-5-1b']
    cdr_5_2a = request.form['cdr-5-2a']
    cdr_5_2b = request.form['cdr-5-2b']
    cdr_5_3 = request.form['cdr-5-3']
    cdr_5_4 = request.form['cdr-5-4']
    cdr_5_5 = request.form['cdr-5-5']
    # cdr 6
    cdr_6_1 = request.form['cdr-6-1']
    cdr_6_2 = request.form['cdr-6-2']
    cdr_6_3 = request.form['cdr-6-3']
    cdr_6_4 = request.form['cdr-6-4']
    # cdr 7
    cdr_7_1 = request.form['cdr-7-1']
    cdr_7_2a = request.form['cdr-7-2a']
    cdr_7_2b = request.form['cdr-7-2b']
    cdr_7_4 = request.form['cdr-7-4']
    cdr_7_5 = request.form['cdr-7-5']
    cdr_7_6a = request.form['cdr-7-6a']
    cdr_7_6b = request.form['cdr-7-6b']
    cdr_7_6c = request.form['cdr-7-6c']
    cdr_7_6d = request.form['cdr-7-6d']
    cdr_7_7 = request.form['cdr-7-7']
    cdr_7_8 = request.form['cdr-7-8']
    cdr_7_9 = request.form['cdr-7-9']
    # cdr 8
    cdr_8_1 = request.form['cdr-8-1']
    cdr_8_2 = request.form['cdr-8-2']
    cdr_8_3 = request.form['cdr-8-3']
    cdr_8_4 = request.form['cdr-8-4']
    cdr_8_5 = request.form['cdr-8-5']
    cdr_8_6 = request.form['cdr-8-6']
    cdr_8_7 = request.form['cdr-8-7']
    cdr_8_8 = request.form['cdr-8-8']
    # cdr 9
    cdr_9_1 = request.form['cdr-9-1']
    cdr_9_2 = request.form['cdr-9-2']
    cdr_9_3 = request.form['cdr-9-3']
    cdr_9_4 = request.form['cdr-9-4']
    cdr_9_5 = request.form['cdr-9-5']
    cdr_9_6 = request.form['cdr-9-6']
    cdr_9_7 = request.form['cdr-9-7']
    cdr_9_8 = request.form['cdr-9-8']
    cdr_9_9 = request.form['cdr-9-9']
    # cdr result
    cdr_res1 = float(request.form['cdr_res1'])
    cdr_res2 = float(request.form['cdr_res2'])
    cdr_res3 = float(request.form['cdr_res3'])
    cdr_res4 = float(request.form['cdr_res4'])
    cdr_res5 = float(request.form['cdr_res5'])
    cdr_res6 = float(request.form['cdr_res6']) 
    hasil_cdr = math.ceil((cdr_res1 + cdr_res2 + cdr_res3 + cdr_res4 + cdr_res5 + cdr_res6) / 6)
    # fetch
    conn = mysql.connect()
    cursor = conn.cursor()
    query = "INSERT INTO tbl_diagnosa (id_pasien, hasil_mmse, hasil_cdr, mmse1, mmse2, mmse3, mmse4, mmse5, mmse6, mmse7, mmse8, mmse9, mmse10, mmse11, cdr_1_1, cdr_1_1a, cdr_1_2, cdr_1_3, cdr_1_4, cdr_1_5, cdr_1_6, cdr_1_7,cdr_1_8, cdr_1_9a, cdr_1_9b, cdr_1_10, cdr_1_11, cdr_1_12a, cdr_1_12b,cdr_1_12c, cdr_1_12d, cdr_1_13, cdr_1_14, cdr_1_15, cdr_2_1, cdr_2_2, cdr_2_3, cdr_2_4, cdr_2_5, cdr_2_6, cdr_2_7, cdr_2_8, cdr_3_1, cdr_3_2, cdr_3_3, cdr_3_4, cdr_3_5, cdr_3_6, cdr_4_1, cdr_4_2, cdr_4_3, cdr_4_4a, cdr_4_4b, cdr_4_5, cdr_4_6, cdr_4_7, cdr_4_8, cdr_4_9, cdr_4_10, cdr_5_1a, cdr_5_1b, cdr_5_2a, cdr_5_2b, cdr_5_3, cdr_5_4, cdr_5_5, cdr_6_1, cdr_6_2, cdr_6_3, cdr_6_4, cdr_7_1, cdr_7_2a, cdr_7_2b, cdr_7_4, cdr_7_5, cdr_7_6a, cdr_7_6b, cdr_7_6c, cdr_7_6d, cdr_7_7, cdr_7_8, cdr_7_9, cdr_8_1, cdr_8_2, cdr_8_3, cdr_8_4, cdr_8_5, cdr_8_6, cdr_8_7, cdr_8_8, cdr_9_1, cdr_9_2, cdr_9_3, cdr_9_4, cdr_9_5, cdr_9_6, cdr_9_7, cdr_9_8, cdr_9_9, cdr_res1, cdr_res2, cdr_res3, cdr_res4, cdr_res5, cdr_res6) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    param = (id_pasien, hasil_mmse, hasil_cdr, mmse1, mmse2, mmse3, mmse4, mmse5, mmse6, mmse7, mmse8, mmse9, mmse10, mmse11, cdr_1_1, cdr_1_1a, cdr_1_2, cdr_1_3, cdr_1_4, cdr_1_5, cdr_1_6, cdr_1_7,cdr_1_8, cdr_1_9a, cdr_1_9b, cdr_1_10, cdr_1_11, cdr_1_12a, cdr_1_12b,cdr_1_12c, cdr_1_12d, cdr_1_13, cdr_1_14, cdr_1_15, cdr_2_1, cdr_2_2, cdr_2_3, cdr_2_4, cdr_2_5, cdr_2_6, cdr_2_7, cdr_2_8, cdr_3_1, cdr_3_2, cdr_3_3, cdr_3_4, cdr_3_5, cdr_3_6, cdr_4_1, cdr_4_2, cdr_4_3, cdr_4_4a, cdr_4_4b, cdr_4_5, cdr_4_6, cdr_4_7, cdr_4_8, cdr_4_9, cdr_4_10, cdr_5_1a, cdr_5_1b, cdr_5_2a, cdr_5_2b, cdr_5_3, cdr_5_4, cdr_5_5, cdr_6_1, cdr_6_2, cdr_6_3, cdr_6_4, cdr_7_1, cdr_7_2a, cdr_7_2b, cdr_7_4, cdr_7_5, cdr_7_6a, cdr_7_6b, cdr_7_6c, cdr_7_6d, cdr_7_7, cdr_7_8, cdr_7_9, cdr_8_1, cdr_8_2, cdr_8_3, cdr_8_4, cdr_8_5, cdr_8_6, cdr_8_7, cdr_8_8, cdr_9_1, cdr_9_2, cdr_9_3, cdr_9_4, cdr_9_5, cdr_9_6, cdr_9_7, cdr_9_8, cdr_9_9, cdr_res1, cdr_res2, cdr_res3, cdr_res4, cdr_res5, cdr_res6)
    cursor.execute(query, param)
    conn.commit()
    # fetch 2
    conn = mysql.connect()
    cursor = conn.cursor()
    query = "UPDATE tbl_pasien SET status_pasien='Sudah Diagnosa' WHERE id_pasien=%s"
    param = (id_pasien)
    cursor.execute(query, param)
    conn.commit()
    return redirect('/pasien')

@app.route('/hasil_diagnosa/<id_pasien>')
def hasil_diagnosa(id_pasien):
    is_login = session.get('logined')
    if is_login == True:
        session['page'] = 'pasien'
        # fetch
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT p.*, d.* FROM tbl_pasien p, tbl_diagnosa d WHERE p.id_pasien=%s AND p.id_pasien = d.id_pasien"
        param = (id_pasien)
        cursor.execute(query, param)
        columns = cursor.description
        result = [{columns[index][0]:column for index,column in enumerate(value)} for value in cursor.fetchall()]
        return flask.render_template('kuesioner_hasil.html', data=result)
    else:
        return redirect('/')

# run the app
app.run()
