from flask import Flask, render_template, request, jsonify
import os, csv
from datetime import date

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, 'blood-banks.csv')
DONORS_PATH = os.path.join(BASE_DIR, 'donors.csv')
DONATIONS_PATH = os.path.join(BASE_DIR, 'donations.csv')
INVENTORY_PATH = os.path.join(BASE_DIR, 'blood_inventory.csv')


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def load_data():
    with open(CSV_PATH, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            clean = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
            rows.append(clean)
        return rows


DATA = load_data()


def val(row, key):
    return row.get(key, '') or ''


def card(row):
    blood_groups = val(row, 'Blood Groups Available (Project Demo)')
    return {
        'id': val(row, 'Sr No'),
        'name': val(row, 'Blood Bank Name'),
        'state': val(row, 'State'),
        'district': val(row, 'District'),
        'city': val(row, 'City'),
        'address': val(row, 'Address').replace('\r\n', ', ').replace('\n', ', '),
        'pincode': val(row, 'Pincode'),
        'contact': val(row, 'Contact No'),
        'mobile': val(row, 'Mobile'),
        'helpline': val(row, 'Helpline'),
        'email': val(row, 'Email'),
        'website': val(row, 'Website'),
        'officer': val(row, 'Nodal Officer'),
        'officer_contact': val(row, 'Contact Nodal Officer'),
        'officer_mobile': val(row, 'Mobile Nodal Officer'),
        'officer_email': val(row, 'Email Nodal Officer'),
        'qualification': val(row, 'Qualification Nodal Officer'),
        'category': val(row, 'Category'),
        'components': val(row, 'Blood Component Available'),
        'apheresis': val(row, 'Apheresis'),
        'service_time': val(row, 'Service Time'),
        'license': val(row, 'License #'),
        'license_date': val(row, 'Date License Obtained'),
        'renewal_date': val(row, 'Date of Renewal'),
        'latitude': val(row, 'Latitude'),
        'longitude': val(row, 'Longitude'),
        'donor_name': val(row, 'Donor Name (Project Demo)'),
        'donor_age': val(row, 'Donor Age (Project Demo)'),
        'donor_gender': val(row, 'Donor Gender (Project Demo)'),
        'donor_blood_group': val(row, 'Donor Blood Group (Project Demo)'),
        'donor_phone': val(row, 'Donor Phone (Project Demo)'),
        'blood_groups': blood_groups,
        'a_pos': val(row, 'A+ Units (Project Demo)'),
        'a_neg': val(row, 'A- Units (Project Demo)'),
        'b_pos': val(row, 'B+ Units (Project Demo)'),
        'b_neg': val(row, 'B- Units (Project Demo)'),
        'o_pos': val(row, 'O+ Units (Project Demo)'),
        'o_neg': val(row, 'O- Units (Project Demo)'),
        'ab_pos': val(row, 'AB+ Units (Project Demo)'),
        'ab_neg': val(row, 'AB- Units (Project Demo)'),
        'total_units': val(row, 'Total Units Available (Project Demo)')
    }


@app.route('/')
def index():
    states = sorted({val(r, 'State') for r in DATA if val(r, 'State')})
    categories = sorted({val(r, 'Category') for r in DATA if val(r, 'Category')})
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
    genders = ['Male', 'Female', 'Other']
    banks = [
        {
            'id': val(r, 'Sr No'),
            'name': val(r, 'Blood Bank Name'),
            'city': val(r, 'City'),
            'state': val(r, 'State')
        }
        for r in DATA
    ]
    return render_template(
        'index.html',
        total=len(DATA),
        states=states,
        categories=categories,
        blood_groups=blood_groups,
        genders=genders,
        banks=banks
    )


@app.route('/api/stats')
def stats():
    states = {val(r, 'State') for r in DATA if val(r, 'State')}
    cities = {val(r, 'City') for r in DATA if val(r, 'City')}
    government = sum(1 for r in DATA if val(r, 'Category').lower() == 'government')
    component = sum(1 for r in DATA if val(r, 'Blood Component Available').upper() == 'YES')
    total_units = sum(int(float(val(r, 'Total Units Available (Project Demo)') or 0)) for r in DATA)
    donors = len({val(r, 'Donor Name (Project Demo)') for r in DATA if val(r, 'Donor Name (Project Demo)')})
    return jsonify({
        'total': len(DATA),
        'states': len(states),
        'cities': len(cities),
        'government': government,
        'component': component,
        'donors': donors,
        'units': total_units
    })


@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip().lower()
    state = request.args.get('state', '').strip().lower()
    category = request.args.get('category', '').strip().lower()
    city = request.args.get('city', '').strip().lower()
    blood_group = request.args.get('blood_group', '').strip().lower()
    gender = request.args.get('gender', '').strip().lower()

    try:
        limit = min(max(int(request.args.get('limit', 100)), 1), 500)
    except ValueError:
        limit = 100

    results = []
    for r in DATA:
        if state and val(r, 'State').lower() != state:
            continue
        if category and val(r, 'Category').lower() != category:
            continue
        if city and val(r, 'City').lower() != city:
            continue
        if blood_group and val(r, 'Donor Blood Group (Project Demo)').lower() != blood_group:
            continue
        if gender and val(r, 'Donor Gender (Project Demo)').lower() != gender:
            continue
        if q:
            hay = ' '.join(str(v or '') for v in r.values()).lower()
            if q not in hay:
                continue
        results.append(card(r))
        if len(results) >= limit:
            break

    return jsonify({'results': results, 'count': len(results)})


@app.route('/api/blood-banks/<int:bank_id>')
def detail(bank_id):
    for r in DATA:
        try:
            if int(float(val(r, 'Sr No'))) == bank_id:
                return jsonify(card(r))
        except (ValueError, TypeError):
            pass
    return jsonify({'error': 'Blood bank not found'}), 404


@app.route('/api/cities')
def cities():
    state = request.args.get('state', '').strip().lower()
    cities = sorted({
        val(r, 'City') for r in DATA
        if (not state or val(r, 'State').lower() == state) and val(r, 'City')
    })
    return jsonify(cities)


@app.route('/api/map')
def map_data():
    results = []
    for r in DATA:
        try:
            lat, lon = float(val(r, 'Latitude')), float(val(r, 'Longitude'))
            results.append({
                'id': val(r, 'Sr No'),
                'name': val(r, 'Blood Bank Name'),
                'city': val(r, 'City'),
                'state': val(r, 'State'),
                'lat': lat,
                'lon': lon
            })
        except (ValueError, TypeError):
            continue
    return jsonify(results[:1000])


def read_csv_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def next_id(path, field):
    rows = read_csv_rows(path)
    ids = []
    for row in rows:
        try:
            ids.append(int(row.get(field, 0)))
        except (TypeError, ValueError):
            pass
    return max(ids, default=0) + 1


def append_csv_row(path, fieldnames, row):
    exists = os.path.exists(path) and os.path.getsize(path) > 0
    with open(path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


@app.route('/api/bank-options')
def bank_options():
    return jsonify([
        {'bank_id': val(r, 'Sr No'), 'bank_name': val(r, 'Blood Bank Name'),
         'city': val(r, 'City'), 'state': val(r, 'State')}
        for r in DATA
    ])


@app.route('/api/donors', methods=['GET'])
def get_donors():
    rows = read_csv_rows(DONORS_PATH)
    return jsonify(rows[-25:][::-1])


@app.route('/api/donors', methods=['POST'])
def add_donor():
    data = request.get_json(silent=True) or {}
    required = ['donor_name', 'age', 'gender', 'blood_group', 'phone', 'city']
    if any(not str(data.get(k, '')).strip() for k in required):
        return jsonify({'error': 'Please fill all donor fields.'}), 400
    try:
        age = int(data['age'])
        if age < 18 or age > 100:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Donor age must be between 18 and 100.'}), 400
    blood_group = str(data['blood_group']).strip().upper()
    if blood_group not in ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']:
        return jsonify({'error': 'Invalid blood group.'}), 400
    donor_id = next_id(DONORS_PATH, 'donor_id')
    row = {
        'donor_id': donor_id,
        'donor_name': str(data['donor_name']).strip(),
        'age': age,
        'gender': str(data['gender']).strip(),
        'blood_group': blood_group,
        'phone': str(data['phone']).strip(),
        'city': str(data['city']).strip()
    }
    append_csv_row(DONORS_PATH, ['donor_id','donor_name','age','gender','blood_group','phone','city'], row)
    return jsonify({'message': 'Donor added successfully.', 'donor': row}), 201


@app.route('/api/donations', methods=['GET'])
def get_donations():
    rows = read_csv_rows(DONATIONS_PATH)
    return jsonify(rows[-25:][::-1])


@app.route('/api/donations', methods=['POST'])
def add_donation():
    data = request.get_json(silent=True) or {}
    required = ['donor_id', 'bank_id', 'donation_date', 'blood_group', 'units_donated']
    if any(not str(data.get(k, '')).strip() for k in required):
        return jsonify({'error': 'Please fill all donation fields.'}), 400
    donor_id = str(data['donor_id']).strip()
    bank_id = str(data['bank_id']).strip()
    if not donor_id.isdigit() or not bank_id.isdigit():
        return jsonify({'error': 'Donor ID and Blood Bank ID must be numbers.'}), 400
    try:
        units = int(data['units_donated'])
        if units < 1 or units > 10:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Units donated must be between 1 and 10.'}), 400
    donation_id = next_id(DONATIONS_PATH, 'donation_id')
    bg = str(data['blood_group']).strip().upper()
    if bg not in ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']:
        return jsonify({'error': 'Invalid blood group.'}), 400
    donor_exists = any(str(r.get('donor_id','')) == donor_id for r in read_csv_rows(DONORS_PATH))
    bank_exists = any(str(r.get('Sr No','')) == bank_id for r in DATA)
    if not donor_exists:
        return jsonify({'error': 'Donor ID not found.'}), 400
    if not bank_exists:
        return jsonify({'error': 'Blood Bank ID not found.'}), 400
    try:
        donation_date = date.fromisoformat(str(data['donation_date']).strip()).isoformat()
    except ValueError:
        return jsonify({'error': 'Donation date must be YYYY-MM-DD.'}), 400
    row = {
        'donation_id': donation_id,
        'donor_id': donor_id,
        'bank_id': bank_id,
        'donation_date': donation_date,
        'blood_group': bg,
        'units_donated': units
    }
    append_csv_row(DONATIONS_PATH, ['donation_id','donor_id','bank_id','donation_date','blood_group','units_donated'], row)
    # Also increase the corresponding inventory record.
    rows = read_csv_rows(INVENTORY_PATH)
    found = False
    for inv in rows:
        if str(inv.get('bank_id','')) == bank_id and inv.get('blood_group','').upper() == bg:
            inv['units_available'] = str(int(inv.get('units_available', 0) or 0) + units)
            found = True
            break
    if found:
        with open(INVENTORY_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['inventory_id','bank_id','blood_group','units_available'])
            writer.writeheader()
            writer.writerows(rows)
    return jsonify({'message': 'Donation recorded and inventory updated.', 'donation': row}), 201


@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    return jsonify(read_csv_rows(INVENTORY_PATH))


@app.route('/api/inventory', methods=['POST'])
def update_inventory():
    data = request.get_json(silent=True) or {}
    required = ['bank_id', 'blood_group', 'units_available']
    if any(not str(data.get(k, '')).strip() for k in required):
        return jsonify({'error': 'Please fill all inventory fields.'}), 400
    bank_id = str(data['bank_id']).strip()
    bg = str(data['blood_group']).strip().upper()
    try:
        units = int(data['units_available'])
        if units < 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Available units must be 0 or more.'}), 400
    if not bank_id.isdigit():
        return jsonify({'error': 'Blood Bank ID must be a number.'}), 400
    bank_exists = any(str(r.get('Sr No','')) == bank_id for r in DATA)
    if not bank_exists:
        return jsonify({'error': 'Blood Bank ID not found.'}), 400
    if bg not in ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']:
        return jsonify({'error': 'Invalid blood group.'}), 400

    rows = read_csv_rows(INVENTORY_PATH)
    found = False
    for inv in rows:
        if str(inv.get('bank_id','')) == bank_id and inv.get('blood_group','').upper() == bg:
            inv['units_available'] = str(units)
            found = True
            break
    if not found:
        next_inv = next_id(INVENTORY_PATH, 'inventory_id')
        rows.append({'inventory_id': next_inv, 'bank_id': bank_id, 'blood_group': bg, 'units_available': units})

    with open(INVENTORY_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['inventory_id','bank_id','blood_group','units_available'])
        writer.writeheader()
        writer.writerows(rows)
    return jsonify({'message': 'Inventory updated successfully.'}), 201


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
