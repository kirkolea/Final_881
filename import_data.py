import os
import csv
from models import db, Subject, Session, AccData, BvpData, EdaData, HrData, TempData, IbiData, TagData

CHUNK_SIZE = 10000

def parse_subject_info(filepath):
    if not os.path.exists(filepath):
        print(f"Warning: Could not find path")
        return
    
    with open(filepath, 'r', encoding='utf-8-sig') as f: 
        reader = csv.DictReader(f)
        
        headers = [h.strip().lower() for h in reader.fieldnames]
        reader.fieldnames = headers

        for row in reader:
            subj_id = row.get('subject_id') or row.get('id') or row.get('subject')
            if not subj_id: 
                continue
            
            subj_id = subj_id.strip()
            
            subj = Subject.query.filter_by(subject_id=subj_id).first()
            if not subj:
                subj = Subject(
                    subject_id=subj_id,
                    age=int(row.get('age', 0)) if row.get('age') and row['age'].strip() else None,
                    weight=float(row.get('weight', 0)) if row.get('weight') and row['weight'].strip() else None,
                    height=float(row.get('height', 0)) if row.get('height') and row['height'].strip() else None
                )
                db.session.add(subj)
        db.session.commit()
        print("Successfully imported subject demographic data.")

def process_standard_sensor(session_id, filepath, model_class, is_acc=False):
    if not os.path.exists(filepath): return
    
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        try:
            next(reader) 
            
            hz_row = next(reader)
            hz = float(hz_row[0])
            
            batch = []
            for i, row in enumerate(reader):
                if not row: continue
                offset = i / hz
                
                if is_acc:
                    batch.append(model_class(session_id=session_id, time_offset=offset, x=float(row[0]), y=float(row[1]), z=float(row[2])))
                else:
                    batch.append(model_class(session_id=session_id, time_offset=offset, value=float(row[0])))
                
                if len(batch) >= CHUNK_SIZE:
                    db.session.bulk_save_objects(batch)
                    batch = []
            
            if batch:
                db.session.bulk_save_objects(batch)
            db.session.commit()
        except Exception as e:
            print(f"Failed parsing {filepath}: {e}")

def process_ibi(session_id, filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        try:
            next(reader)
            batch = []
            for row in reader:
                if len(row) >= 2:
                    try:
                        batch.append(IbiData(session_id=session_id, time_offset=float(row[0]), duration=float(row[1])))
                    except ValueError:
                        continue
                if len(batch) >= CHUNK_SIZE:
                    db.session.bulk_save_objects(batch)
                    batch = []
            if batch:
                db.session.bulk_save_objects(batch)
            db.session.commit()
        except Exception as e:
            pass

def process_tags(session_id, filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        batch = []
        for row in reader:
            if row:
                try:
                    batch.append(TagData(session_id=session_id, timestamp=float(row[0])))
                except ValueError:
                    continue
        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()

def build_database(app, root_dir):
    with app.app_context():
        db.create_all()
        
        dataset_dir = os.path.join(root_dir, 'Wearable_Dataset')
        if not os.path.exists(dataset_dir):
            print(f"CRITICAL ERROR: Could not find {dataset_dir}")
            return
            
        info_file = os.path.join(dataset_dir, 'subject-info.csv')
        parse_subject_info(info_file)

        conditions = ['AEROBIC', 'ANAEROBIC', 'STRESS']
        
        for condition in conditions:
            cond_path = os.path.join(dataset_dir, condition)
            if not os.path.exists(cond_path): continue
            
            for subj_id in os.listdir(cond_path):
                subj_path = os.path.join(cond_path, subj_id)
                if not os.path.isdir(subj_path): continue

                print(f"Processing Subject: {subj_id} | Condition: {condition}")

                subj = Subject.query.filter_by(subject_id=subj_id).first()
                if not subj:
                    subj = Subject(subject_id=subj_id)
                    db.session.add(subj)
                    db.session.commit()

                sess = Session(subject_id=subj_id, condition=condition)
                db.session.add(sess)
                db.session.commit()

                process_standard_sensor(sess.id, os.path.join(subj_path, 'ACC.csv'), AccData, is_acc=True)
                process_standard_sensor(sess.id, os.path.join(subj_path, 'BVP.csv'), BvpData)
                process_standard_sensor(sess.id, os.path.join(subj_path, 'EDA.csv'), EdaData)
                process_standard_sensor(sess.id, os.path.join(subj_path, 'HR.csv'), HrData)
                process_standard_sensor(sess.id, os.path.join(subj_path, 'TEMP.csv'), TempData)
                process_ibi(sess.id, os.path.join(subj_path, 'IBI.csv'))
                process_tags(sess.id, os.path.join(subj_path, 'tags.csv'))
        
        print("Database import complete.")