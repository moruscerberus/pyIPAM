from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import ipaddress
import os
import socket
import subprocess
import threading
import platform
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pyipam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.static_folder = 'static'
app.template_folder = 'templates'

db = SQLAlchemy(app)

# Global scan status tracker
scan_status = {}  # {subnet_id: {'scanning': True, 'current_ip': 'x.x.x.x'}}

class Subnet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cidr = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    ips = db.relationship('IPAddress', backref='subnet', lazy=True)

class IPAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), nullable=False)
    status = db.Column(db.String(10), default='free')  # free, used, reserved
    hostname = db.Column(db.String(100))
    description = db.Column(db.String(200))
    subnet_id = db.Column(db.Integer, db.ForeignKey('subnet.id'), nullable=False)

@app.route('/')
def index():
    subnets = Subnet.query.all()

    for subnet in subnets:
        total_ips = len(subnet.ips)
        used_ips = len([ip for ip in subnet.ips if ip.status == 'used'])

        # Calculate percentage of used IPs and round it to 2 decimal places
        subnet.used_percentage = round((used_ips / total_ips) * 100, 2) if total_ips > 0 else 0

        # Check for IP conflicts (IPs that share the same hostname)
        conflicts = db.session.query(IPAddress.hostname).filter_by(subnet_id=subnet.id).group_by(IPAddress.hostname).having(db.func.count(IPAddress.id) > 1).all()
        subnet.ip_conflict = len(conflicts) > 0

    return render_template('index.html', subnets=subnets)


@app.route('/subnet/<int:subnet_id>/conflicts')
def view_conflicts(subnet_id):
    subnet = Subnet.query.get_or_404(subnet_id)

    # Find IP addresses with duplicate hostnames within the same subnet
    conflicts = db.session.query(IPAddress).filter_by(subnet_id=subnet.id).filter(IPAddress.hostname.in_(
        db.session.query(IPAddress.hostname).filter_by(subnet_id=subnet.id).group_by(IPAddress.hostname).having(db.func.count(IPAddress.id) > 1)
    )).all()

    # Return to the view_conflicts page with the conflicting IPs
    return render_template('view_conflicts.html', subnet=subnet, conflicts=conflicts)

@app.route('/add_subnet', methods=['POST'])
def add_subnet():
    cidr = request.form['cidr']
    description = request.form.get('description', '')  # Default to empty string if not provided
    try:
        # Validate and create the IP network from the CIDR
        ip_net = ipaddress.ip_network(cidr, strict=False)
        new_subnet = Subnet(cidr=str(ip_net), description=description)
        
        # Add subnet to the database
        db.session.add(new_subnet)
        db.session.commit()

        # Add IP addresses for the subnet
        for ip in ip_net.hosts():
            new_ip = IPAddress(ip=str(ip), subnet=new_subnet)
            db.session.add(new_ip)

        db.session.commit()

        # Redirect to the index page to show all subnets
        return redirect(url_for('index'))

    except ValueError:
        return "Invalid CIDR", 400

@app.route('/subnet/<int:subnet_id>')
def view_subnet(subnet_id):
    subnet = Subnet.query.get_or_404(subnet_id)
    page = request.args.get('page', 1, type=int)
    per_page = 50  # Customize pagination size
    paginated_ips = IPAddress.query.filter_by(subnet_id=subnet.id).paginate(page=page, per_page=per_page)
    return render_template('subnet_detail.html', subnet=subnet, paginated_ips=paginated_ips)

@app.route('/update_ip/<int:ip_id>', methods=['POST'])
def update_ip(ip_id):
    ip = IPAddress.query.get_or_404(ip_id)
    ip.status = request.form['status']
    ip.hostname = request.form.get('hostname', '')
    ip.description = request.form.get('description', '')
    db.session.commit()
    return redirect(url_for('view_subnet', subnet_id=ip.subnet_id))

@app.route('/scan_subnet/<int:subnet_id>', methods=['POST'])
def scan_subnet(subnet_id):
    threading.Thread(target=scan, args=(app, subnet_id)).start()
    return redirect(url_for('view_subnet', subnet_id=subnet_id))

@app.route('/scan_status/<int:subnet_id>')
def scan_status_view(subnet_id):
    return jsonify(scan_status.get(subnet_id, {'scanning': False}))

def scan(app, subnet_id):
    with app.app_context():
        subnet = Subnet.query.get_or_404(subnet_id)
        is_windows = platform.system().lower() == 'windows'
        ping_cmd = ['ping', '-n', '1'] if is_windows else ['ping', '-c', '1', '-W', '1']

        scan_status[subnet_id] = {'scanning': True, 'current_ip': ''}
        for ip in subnet.ips:
            try:
                scan_status[subnet_id]['current_ip'] = ip.ip
                result = subprocess.run(ping_cmd + [ip.ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if result.returncode == 0:
                    ip.status = 'used'
                    try:
                        ip.hostname = socket.gethostbyaddr(ip.ip)[0]
                        print(f"Resolved {ip.ip} to {ip.hostname}")
                    except socket.herror:
                        ip.hostname = ''
                else:
                    ip.status = 'free'
                db.session.commit()
            except Exception as e:
                print(f"Error scanning {ip.ip}: {e}")
        scan_status[subnet_id] = {'scanning': False, 'current_ip': ''}

# Scheduled background scanning
def scan_all_subnets():
    with app.app_context():
        all_subnets = Subnet.query.all()
        for subnet in all_subnets:
            threading.Thread(target=scan, args=(app, subnet.id)).start()

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(scan_all_subnets, 'interval', minutes=15)  # Auto-scan every 15 minutes
scheduler.start()

if __name__ == '__main__':
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
