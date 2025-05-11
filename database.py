import pymysql
import psycopg2
import psycopg2.extras
import json
import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, NumberRange, Length
from models import DatabaseConnection, Query
from extensions import db
from ai import generate_sql_query, generate_natural_language_result

db_bp = Blueprint('db_bp', __name__)

class ConnectionForm(FlaskForm):
    """Form for database connection details"""
    name = StringField('Connection Name', validators=[DataRequired(), Length(max=64)])
    db_type = SelectField('Database Type', 
                          choices=[('mysql', 'MySQL'), 
                                   ('postgresql', 'PostgreSQL')], 
                          default='mysql')
    host = StringField('Host', validators=[DataRequired(), Length(max=128)])
    port = IntegerField('Port', validators=[DataRequired(), NumberRange(min=1, max=65535)], default=3306)
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    database_name = StringField('Database Name', validators=[DataRequired(), Length(max=64)])
    submit = SubmitField('Connect')

class QueryForm(FlaskForm):
    """Form for natural language query input"""
    query = TextAreaField('Ask a question about your database in plain English', 
                         validators=[DataRequired(), Length(min=10, max=1000)])
    submit = SubmitField('Generate SQL and Run Query')

@db_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page showing user's database connections"""
    connections = DatabaseConnection.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', connections=connections)

@db_bp.route('/test-connection', methods=['POST'])
@login_required
def test_connection():
    """Test database connection without saving"""
    try:
        data = request.json
        
        # Validate inputs
        if not data.get('host') or not data.get('username') or not data.get('database_name'):
            return jsonify({
                'success': False,
                'error': 'Missing required connection parameters'
            })
        
        db_type = data.get('db_type', 'mysql').lower()
        tables = []
        password = data.get('password', '')
        
        # Using plain password from form for initial connection test
        if db_type == 'mysql':
            # Connect to MySQL
            connection = pymysql.connect(
                host=data.get('host'),
                user=data.get('username'),
                password=password,
                db=data.get('database_name'),
                port=int(data.get('port', 3306)),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10  # Add timeout to avoid long waits
            )
            
            # Get table list to verify connection works
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [list(table.values())[0] for table in cursor.fetchall()]
            
            connection.close()
            
        elif db_type == 'postgresql':
            # Connect to PostgreSQL
            connection = psycopg2.connect(
                host=data.get('host'),
                user=data.get('username'),
                password=password,  # Using password from the earlier extraction
                dbname=data.get('database_name'),
                port=int(data.get('port', 5432)),
                connect_timeout=10,  # Add timeout to avoid long waits
            )
            
            # Get table list to verify connection works
            with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [record['table_name'] for record in cursor.fetchall()]
            
            connection.close()
        
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported database type: {db_type}'
            })
        
        return jsonify({
            'success': True,
            'tables': tables,
            'db_type': db_type,
            'message': f'Successfully connected to {db_type.upper()} database "{data.get("database_name")}" with {len(tables)} tables.'
        })
        
    except pymysql.err.OperationalError as e:
        # Handle MySQL errors
        error_code = e.args[0]
        error_message = str(e)
        
        if error_code == 1045:  # Access denied error
            client_ip = request.remote_addr
            additional_info = (
                f"Access denied to MySQL server. This might be due to incorrect credentials "
                f"or IP restrictions. The Replit server IP address ({client_ip}) may need to be "
                f"whitelisted in your database's security settings."
            )
            error_message = f"{error_message}. {additional_info}"
        elif error_code == 2003:  # Can't connect error
            error_message = f"Cannot connect to MySQL server at '{data.get('host')}:{data.get('port', 3306)}'. "
            error_message += "Please verify the hostname and port, and ensure the database server is running."
            
        return jsonify({
            'success': False,
            'error': error_message
        })
    except psycopg2.OperationalError as e:
        # Handle PostgreSQL errors
        error_message = str(e)
        client_ip = request.remote_addr
        
        if "password authentication failed" in error_message.lower():
            additional_info = "Authentication failed. Please check your username and password."
            error_message = f"{error_message}. {additional_info}"
        elif "could not connect to server" in error_message.lower():
            error_message = f"Cannot connect to PostgreSQL server at '{data.get('host')}:{data.get('port', 5432)}'. "
            error_message += "Please verify the hostname and port, and ensure the database server is running."
        
        return jsonify({
            'success': False,
            'error': f"PostgreSQL error: {error_message}"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error connecting to database: {str(e)}"
        })

@db_bp.route('/connect', methods=['GET', 'POST'])
@login_required
def connect_db():
    """Connect to a new database"""
    form = ConnectionForm()
    
    if form.validate_on_submit():
        # Test connection before saving
        try:
            # Handle different database types
            db_type = form.db_type.data.lower()
            
            if db_type == 'mysql':
                # Test MySQL connection
                connection = pymysql.connect(
                    host=form.host.data,
                    user=form.username.data,
                    password=form.password.data,
                    db=form.database_name.data,
                    port=form.port.data,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                connection.close()
            elif db_type == 'postgresql':
                # Test PostgreSQL connection
                connection = psycopg2.connect(
                    host=form.host.data,
                    user=form.username.data,
                    password=form.password.data,
                    dbname=form.database_name.data,
                    port=form.port.data,
                    connect_timeout=10
                )
                connection.close()
            else:
                flash(f'Unsupported database type: {db_type}', 'danger')
                return render_template('connect_db.html', form=form)
            
            # Connection successful, save to database
            db_connection = DatabaseConnection(
                name=form.name.data,
                host=form.host.data,
                port=form.port.data,
                username=form.username.data,
                database_name=form.database_name.data,
                user_id=current_user.id,
                db_type=db_type
            )
            db_connection.set_password(form.password.data)
            
            db.session.add(db_connection)
            db.session.commit()
            
            flash(f'{db_type.upper()} database connection created successfully!', 'success')
            return redirect(url_for('db_bp.dashboard'))
            
        except (pymysql.err.OperationalError, psycopg2.OperationalError) as e:
            flash(f'Error connecting to database: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Unexpected error: {str(e)}', 'danger')
    
    # If we're reaching this point and there's a passed DATABASE_URL in the environment,
    # pre-populate the form with PostgreSQL info from the environment
    if not form.is_submitted() and os.environ.get('DATABASE_URL'):
        # Default to PostgreSQL settings from environment
        form.db_type.data = 'postgresql'
        form.host.data = os.environ.get('PGHOST', 'localhost')
        form.port.data = int(os.environ.get('PGPORT', 5432))
        form.username.data = os.environ.get('PGUSER', '')
        form.database_name.data = os.environ.get('PGDATABASE', '')
    
    return render_template('connect_db.html', form=form)

@db_bp.route('/connection/<int:conn_id>')
@login_required
def connection_detail(conn_id):
    """View connection details and previous queries"""
    connection = DatabaseConnection.query.filter_by(id=conn_id, user_id=current_user.id).first_or_404()
    queries = Query.query.filter_by(connection_id=conn_id).order_by(Query.created_at.desc()).all()
    form = QueryForm()
    
    return render_template('query.html', connection=connection, queries=queries, form=form)

@db_bp.route('/connection/<int:conn_id>/delete', methods=['POST'])
@login_required
def delete_connection(conn_id):
    """Delete a database connection"""
    connection = DatabaseConnection.query.filter_by(id=conn_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(connection)
    db.session.commit()
    
    flash('Connection deleted successfully', 'success')
    return redirect(url_for('db_bp.dashboard'))

@db_bp.route('/connection/<int:conn_id>/query', methods=['POST'])
@login_required
def query(conn_id):
    """Process a natural language query"""
    connection = DatabaseConnection.query.filter_by(id=conn_id, user_id=current_user.id).first_or_404()
    form = QueryForm()
    
    if form.validate_on_submit():
        natural_language_query = form.query.data
        
        try:
            # First, get database schema
            try:
                schema_info = get_database_schema(connection)
            except Exception as db_err:
                db_type = connection.db_type.upper()
                error_msg = str(db_err)
                
                # Add more user-friendly error messages
                if "Access denied" in error_msg or "password authentication failed" in error_msg:
                    return jsonify({
                        'success': False,
                        'error': f"{db_type} connection error: Authentication failed. Please check your credentials and try again."
                    })
                elif "cannot connect to server" in error_msg or "Can't connect" in error_msg:
                    return jsonify({
                        'success': False, 
                        'error': f"{db_type} connection error: Cannot connect to the database server. The server might be down or unreachable."
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f"{db_type} connection error: {error_msg}"
                    })
            
            # Generate SQL using OpenAI with appropriate database syntax
            sql_query = generate_sql_query(
                natural_language_query, 
                schema_info,
                db_type=connection.db_type
            )
            
            # Execute the SQL query
            try:
                result = execute_sql_query(connection, sql_query)
            except Exception as sql_err:
                error_msg = str(sql_err)
                
                if "syntax error" in error_msg.lower():
                    return jsonify({
                        'success': False,
                        'error': f"SQL Error: Syntax error in the generated query. Please try rephrasing your question.",
                        'sql': sql_query,
                        'details': error_msg
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f"Error executing query: {error_msg}",
                        'sql': sql_query
                    })
            
            # Generate natural language response
            nl_result = generate_natural_language_result(natural_language_query, sql_query, result)
            
            # Save the query
            query = Query(
                natural_language=natural_language_query,
                sql_query=sql_query,
                result=json.dumps(result),
                natural_language_result=nl_result,
                connection_id=conn_id
            )
            db.session.add(query)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'query_id': query.id,
                'sql': sql_query,
                'result': result,
                'explanation': nl_result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f"An unexpected error occurred: {str(e)}"
            }), 500
    
    return jsonify({
        'success': False,
        'error': 'Invalid form submission'
    }), 400

@db_bp.route('/query/<int:query_id>')
@login_required
def query_detail(query_id):
    """View details of a specific query"""
    query = Query.query.filter_by(id=query_id).first_or_404()
    connection = DatabaseConnection.query.filter_by(id=query.connection_id, user_id=current_user.id).first_or_404()
    
    return render_template(
        'query_detail.html', 
        query=query, 
        connection=connection,
        result=json.loads(query.result) if query.result else None
    )

def get_database_schema(connection):
    """Retrieve schema information from the database"""
    try:
        schema_info = {}
        
        # Get password and handle different formats
        password = connection.get_password()
        
        # Handle issue with encrypted passwords vs hashed passwords
        if ':' in connection.password_hash and password == connection.password_hash:
            # Using old password hash method, just use the raw password hash
            # This is a temporary fix for backward compatibility
            password = connection.password_hash
            
        # Handle different database types
        if connection.is_mysql:
            # MySQL connection
            conn = pymysql.connect(
                host=connection.host,
                user=connection.username,
                password=password,
                db=connection.database_name,
                port=connection.port,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10  # Add timeout to avoid long waits
            )
            
            with conn.cursor() as cursor:
                # Get all tables
                cursor.execute("SHOW TABLES")
                tables = [list(table.values())[0] for table in cursor.fetchall()]
                
                # Get columns for each table
                for table in tables:
                    cursor.execute(f"DESCRIBE `{table}`")
                    columns = cursor.fetchall()
                    schema_info[table] = columns
            
            conn.close()
            
        elif connection.is_postgresql:
            # PostgreSQL connection
            conn = psycopg2.connect(
                host=connection.host,
                user=connection.username,
                password=password,  # Use the processed password
                dbname=connection.database_name,
                port=connection.port,
                connect_timeout=10
            )
            
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Get all tables from public schema
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [record['table_name'] for record in cursor.fetchall()]
                
                # Get columns for each table
                for table in tables:
                    cursor.execute(f"""
                        SELECT column_name, data_type, 
                               CASE WHEN is_nullable = 'YES' THEN 'YES' ELSE 'NO' END AS is_nullable,
                               CASE WHEN column_default IS NOT NULL THEN column_default ELSE '' END AS column_default
                        FROM information_schema.columns
                        WHERE table_name = '{table}' AND table_schema = 'public'
                    """)
                    # Convert to a format similar to MySQL's DESCRIBE
                    columns = []
                    for col in cursor.fetchall():
                        columns.append({
                            'Field': col['column_name'],
                            'Type': col['data_type'],
                            'Null': col['is_nullable'],
                            'Default': col['column_default'],
                            'Key': '',  # PostgreSQL doesn't directly expose this in information_schema
                            'Extra': ''
                        })
                    schema_info[table] = columns
            
            conn.close()
        else:
            raise Exception(f"Unsupported database type: {connection.db_type}")
            
        return schema_info
        
    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:  # Access denied error
            error_message = (
                f"Access denied to MySQL database '{connection.database_name}' on host '{connection.host}'. "
                f"Please verify your credentials and ensure that this server's IP address "
                f"is allowed in your database's access control settings."
            )
            raise Exception(error_message)
        elif error_code == 2003:  # Can't connect error
            raise Exception(f"Cannot connect to MySQL server at '{connection.host}:{connection.port}'. "
                          f"Please verify the hostname and port, and ensure the database server is running.")
        else:
            raise Exception(f"Database connection error ({error_code}): {str(e)}")
    except psycopg2.OperationalError as e:
        error_message = str(e)
        if "password authentication failed" in error_message.lower():
            raise Exception(f"Authentication failed for PostgreSQL database. Please check your credentials.")
        elif "could not connect to server" in error_message.lower():
            raise Exception(f"Cannot connect to PostgreSQL server at '{connection.host}:{connection.port}'. "
                          f"Please verify the hostname and port, and ensure the database server is running.")
        else:
            raise Exception(f"PostgreSQL error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error fetching database schema: {str(e)}")

def execute_sql_query(connection, sql_query):
    """Execute SQL query against the database"""
    conn = None
    try:
        password = connection.get_password()
        
        # Handle issue with encrypted passwords vs hashed passwords
        if ':' in connection.password_hash and password == connection.password_hash:
            # Using old password hash method, just use the raw hash for now
            password = connection.password_hash
        
        # Handle different database types
        if connection.is_mysql:
            # MySQL connection
            conn = pymysql.connect(
                host=connection.host,
                user=connection.username,
                password=password,
                db=connection.database_name,
                port=connection.port,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10  # Add timeout to avoid long waits
            )
            
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                
                # For SELECT queries, return results
                if sql_query.strip().lower().startswith('select'):
                    result = cursor.fetchall()
                    return result
                # For other queries, return affected row count
                else:
                    conn.commit()
                    return {'affected_rows': cursor.rowcount}
            
        elif connection.is_postgresql:
            # PostgreSQL connection
            conn = psycopg2.connect(
                host=connection.host,
                user=connection.username,
                password=password,  # Use the processed password
                dbname=connection.database_name,
                port=connection.port,
                connect_timeout=10
            )
            
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(sql_query)
                
                # For SELECT queries, return results
                if sql_query.strip().lower().startswith('select'):
                    result = cursor.fetchall()
                    # Convert psycopg2 result to dict list to match MySQL format
                    dict_result = []
                    for row in result:
                        dict_result.append(dict(row))
                    return dict_result
                # For other queries, return affected row count
                else:
                    conn.commit()
                    return {'affected_rows': cursor.rowcount}
        
        else:
            raise Exception(f"Unsupported database type: {connection.db_type}")
        
    except pymysql.err.OperationalError as e:
        # Handle MySQL errors
        error_code = e.args[0]
        if error_code == 1045:  # Access denied error
            error_message = (
                f"Access denied to MySQL database '{connection.database_name}' on host '{connection.host}'. "
                f"Please verify your credentials and ensure that this server's IP address "
                f"is allowed in your database's access control settings."
            )
            raise Exception(error_message)
        elif error_code == 2003:  # Can't connect error
            raise Exception(f"Cannot connect to MySQL server at '{connection.host}:{connection.port}'. "
                          f"Please verify the hostname and port, and ensure the database server is running.")
        else:
            raise Exception(f"Database connection error ({error_code}): {str(e)}")
    except pymysql.err.ProgrammingError as e:
        raise Exception(f"MySQL syntax error: {str(e)}")
    except psycopg2.OperationalError as e:
        # Handle PostgreSQL connection errors
        error_message = str(e)
        if "password authentication failed" in error_message.lower():
            raise Exception(f"Authentication failed for PostgreSQL database. Please check your credentials.")
        elif "could not connect to server" in error_message.lower():
            raise Exception(f"Cannot connect to PostgreSQL server at '{connection.host}:{connection.port}'. "
                          f"Please verify the hostname and port, and ensure the database server is running.")
        else:
            raise Exception(f"PostgreSQL error: {str(e)}")
    except psycopg2.ProgrammingError as e:
        # Handle PostgreSQL syntax errors
        raise Exception(f"PostgreSQL syntax error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error executing query: {str(e)}")
    finally:
        if conn:
            conn.close()
