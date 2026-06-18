"""
Management command: python manage.py seed
Creates sample users, sessions, assessments, rings, reports, and payouts for demo.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import uuid, random


class Command(BaseCommand):
    help = 'Seed the database with sample Tutlee data'

    def handle(self, *args, **options):
        from accounts.models import User, TutorProfile, LearnerProfile
        from sessions_app.models import Session, SessionRating
        from assessments.models import Assessment
        from kyt.models import KYTApplication
        from study_rings.models import StudyRing
        from reports.models import Report
        from payments.models import Transaction, PayoutRequest

        self.stdout.write('Seeding Tutlee database...')

        # ── ADMIN ──
        admin, _ = User.objects.get_or_create(
            email='admin@tutlee.com',
            defaults=dict(username='admin', first_name='Tutlee', last_name='Admin',
                          role='admin', is_staff=True, is_superuser=True)
        )
        admin.set_password('admin123')
        admin.save()
        self.stdout.write(f'  Admin: admin@tutlee.com / admin123')

        # ── TUTORS ──
        tutors_data = [
            dict(email='kwame@tutlee.com',  first_name='Dr. Kwame',   last_name='Adu',
                 subjects=['Mathematics','Physics'], specialities=['Calculus','Mechanics'],
                 hourly_rate=40, rating=4.9, sessions=142, pass_rate=82),
            dict(email='nana@tutlee.com',   first_name='Prof. Nana',  last_name='Boateng',
                 subjects=['Physics','Chemistry'], specialities=['Thermodynamics','Quantum'],
                 hourly_rate=35, rating=4.7, sessions=98,  pass_rate=76),
            dict(email='ama@tutlee.com',    first_name='Mrs. Ama',    last_name='Sarpong',
                 subjects=['English','Literature'], specialities=['Essay Writing','Grammar'],
                 hourly_rate=30, rating=4.8, sessions=67,  pass_rate=79),
            dict(email='joseph@tutlee.com', first_name='Mr. Joseph',  last_name='Owusu',
                 subjects=['Chemistry','Biology'], specialities=['Organic Chemistry','Cell Biology'],
                 hourly_rate=32, rating=4.5, sessions=34,  pass_rate=71),
        ]
        tutor_users = []
        for d in tutors_data:
            subjects    = d.pop('subjects')
            specialities = d.pop('specialities')
            hourly_rate = d.pop('hourly_rate')
            rating      = d.pop('rating')
            sessions    = d.pop('sessions')
            pass_rate   = d.pop('pass_rate')
            u, created = User.objects.get_or_create(email=d['email'], defaults={**d, 'username': d['email'].split('@')[0], 'role':'tutor'})
            if created:
                u.set_password('tutor123')
                u.save()
            tp, _ = TutorProfile.objects.get_or_create(user=u)
            tp.subjects       = subjects
            tp.specialities   = specialities
            tp.hourly_rate    = hourly_rate
            tp.rating         = rating
            tp.total_sessions = sessions
            tp.pass_rate      = pass_rate
            tp.save()
            KYTApplication.objects.get_or_create(
                tutor=u, defaults=dict(
                    interview_done=True,
                    proficiency_score=random.randint(72, 95),
                    status='approved',
                    reviewed_by=admin,
                    reviewed_at=timezone.now(),
                )
            )
            tutor_users.append(u)
            self.stdout.write(f'  Tutor: {u.email} / tutor123')

        # ── LEARNERS ──
        learners_data = [
            dict(email='amara@tutlee.com',   first_name='Amara',   last_name='Osei',    subjects=['Mathematics','Physics']),
            dict(email='zara@tutlee.com',    first_name='Zara',    last_name='Mensah',  subjects=['Physics','Chemistry']),
            dict(email='kofi@tutlee.com',    first_name='Kofi',    last_name='Asante',  subjects=['English']),
            dict(email='efua@tutlee.com',    first_name='Efua',    last_name='Darko',   subjects=['Chemistry','Biology']),
            dict(email='abena@tutlee.com',   first_name='Abena',   last_name='Frimpong',subjects=['Mathematics']),
        ]
        learner_users = []
        for d in learners_data:
            subjects = d.pop('subjects')
            u, created = User.objects.get_or_create(email=d['email'], defaults={**d, 'username': d['email'].split('@')[0], 'role':'learner'})
            if created:
                u.set_password('learner123')
                u.save()
            lp, _ = LearnerProfile.objects.get_or_create(user=u)
            lp.subjects = subjects
            lp.save()
            learner_users.append(u)
            self.stdout.write(f'  Learner: {u.email} / learner123')

        # ── SESSIONS ──
        subjects_list = ['Mathematics', 'Physics', 'Chemistry', 'English', 'Biology']
        statuses = ['completed', 'completed', 'completed', 'cancelled', 'live']
        for i in range(12):
            learner = random.choice(learner_users)
            tutor   = random.choice(tutor_users)
            subj    = random.choice(subjects_list)
            stat    = random.choice(statuses)
            delta   = timedelta(days=random.randint(0, 14))
            s, created = Session.objects.get_or_create(
                learner=learner, tutor=tutor, subject=subj,
                scheduled_at=timezone.now() - delta,
                defaults=dict(status=stat, amount=random.choice([25,30,35,40]), duration_mins=60)
            )
            if created and stat == 'completed':
                # Add rating
                SessionRating.objects.get_or_create(
                    session=s, rater=learner,
                    defaults=dict(
                        punctuality=random.randint(3,5),
                        explanation=random.randint(3,5),
                        overall=random.randint(3,5),
                    )
                )
                # Add assessment
                questions = [
                    {'text': f'Sample question {j+1} for {subj}?',
                     'options': ['Option A','Option B','Option C','Option D'],
                     'answer': random.randint(0,3)} for j in range(5)
                ]
                passed = random.random() > 0.3
                answers = [q['answer'] if passed else (q['answer']+1)%4 for q in questions]
                Assessment.objects.get_or_create(
                    session=s, learner=learner,
                    defaults=dict(
                        subject=subj, questions=questions, answers=answers,
                        score=round(random.uniform(55,95) if passed else random.uniform(20,59), 1),
                        passed=passed, status='completed',
                        completed_at=timezone.now() - delta + timedelta(hours=2),
                        suggestion='Great work! Book your next session.' if passed else 'Consider rebooking to revisit weak areas.',
                    )
                )
                # Transaction
                Transaction.objects.get_or_create(
                    reference=f'TXN-SESSION-{s.id}',
                    defaults=dict(user=learner, type='session_payment', amount=s.amount, status='settled', session=s)
                )

        # ── KYT PENDING ──
        pending_data = [
            dict(email='ama.kyei@tutlee.com', first_name='Dr. Ama', last_name='Kyei', score=82),
            dict(email='felix@tutlee.com',    first_name='Mr. Felix', last_name='Yeboah', score=91),
        ]
        for d in pending_data:
            score = d.pop('score')
            u, created = User.objects.get_or_create(email=d['email'], defaults={**d, 'username': d['email'].split('@')[0], 'role':'tutor'})
            if created:
                u.set_password('tutor123')
                u.save()
            TutorProfile.objects.get_or_create(user=u)
            KYTApplication.objects.get_or_create(tutor=u, defaults=dict(proficiency_score=score, status='pending'))

        # ── STUDY RINGS ──
        rings_data = [
            dict(name='WASSCE Prep 2026', subject='Multi-subject', description='Comprehensive WASSCE preparation for all core subjects.', color='#0D9488'),
            dict(name='A-Level Maths Hub', subject='Mathematics', description='Advanced level mathematics problem solving and discussion.', color='#6366F1'),
            dict(name='IGCSE Science', subject='Sciences', description='Physics, Chemistry, and Biology for IGCSE students.', color='#F97316'),
        ]
        for d in rings_data:
            color = d.pop('color')
            ring, created = StudyRing.objects.get_or_create(
                name=d['name'],
                defaults={**d, 'creator': admin, 'avatar_color': color, 'is_featured': True}
            )
            if created:
                for u in learner_users[:3]:
                    ring.members.add(u)

        # ── REPORTS ──
        if learner_users and tutor_users:
            Report.objects.get_or_create(
                reporter=learner_users[0], accused=tutor_users[-1], type='harassment',
                defaults=dict(description='Tutor made inappropriate remarks during the session.', status='open')
            )

        # ── PAYOUT REQUESTS ──
        for t in tutor_users[:2]:
            try:
                tp = t.tutor_profile
                tp.balance = random.uniform(200, 800)
                tp.save()
                PayoutRequest.objects.get_or_create(
                    tutor=t, status='pending',
                    defaults=dict(
                        sessions_count=random.randint(5,20),
                        gross=float(tp.balance),
                        platform_fee=round(float(tp.balance)*0.15, 2),
                        net=round(float(tp.balance)*0.85, 2),
                    )
                )
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS('\nSeed complete! Log in with any of the accounts above.'))
