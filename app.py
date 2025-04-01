from flask import Flask, request, render_template
from vaccine_recommender import VaccineRecommender

app = Flask(__name__)
recommender = VaccineRecommender("data/nip_schedule.json", "data/iap_schedule.json")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            age_value = request.form.get('age_value', '0')
            age_unit = request.form.get('age_unit', 'weeks')
            include_iap = request.form.get('include_iap', 'off') == 'on'

            if not age_value or not age_value.replace('.', '').isdigit():
                raise ValueError("Please enter a valid age number")
            
            age_value = float(age_value)
            if age_value < 0:
                raise ValueError("Age cannot be negative")

            # Convert to days
            if age_unit == 'hours':
                age_days = age_value / 24
            elif age_unit == 'days':
                age_days = age_value
            elif age_unit == 'weeks':
                age_days = age_value * 7
            elif age_unit == 'months':
                age_days = age_value * 30
            elif age_unit == 'years':
                age_days = age_value * 365
            else:
                age_days = 0
                
            nip_recs = recommender.get_nip_recommendations(age_days)
            iap_recs = recommender.get_iap_recommendations(age_days) if include_iap else []
            
            return render_template('results.html', 
                                age=f"{age_value} {age_unit}",
                                nip_recommendations=nip_recs,
                                iap_recommendations=iap_recs,
                                include_iap=include_iap)
            
        except Exception as e:
            return render_template('index.html', error=str(e)), 400
    
    return render_template('index.html')

@app.route('/schedule')
def full_schedule():
    try:
        schedule_type = request.args.get('type', 'nip')
        if schedule_type not in ['nip', 'iap']:
            raise ValueError("Invalid schedule type")
            
        formatted = recommender.get_formatted_schedule(schedule_type)
        return render_template('schedule.html', 
                            schedule=formatted,
                            schedule_type=schedule_type.upper())
    except Exception as e:
        return render_template('error.html', error=str(e)), 400

@app.route('/compare')
def compare_schedules():
    try:
        schedules = recommender.get_all_schedules()
        return render_template('compare.html',
                            nip_schedule=schedules["nip"],
                            iap_schedule=schedules["iap"],
                            categories=schedules["iap_categories"])
    except Exception as e:
        return render_template('error.html', error=str(e)), 400

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found"), 404

if __name__ == '__main__':
    app.run(debug=True)