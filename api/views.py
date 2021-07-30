import time

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout, authenticate
from api import models
from workoutnote_django import models as wn_models
from datetime import datetime, timedelta


# region auth
@require_http_methods(['POST'])
def handle_login_api(request):
    required_params = ['email', 'password']
    if False not in [x in request.POST for x in required_params]:
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(username=email, password=password)
        if user and user.is_authenticated:
            login(request=request, user=user)
            if not models.SessionKey.objects.filter(user=user).exists():
                session_key = models.SessionKey.generate_key(email=email)
                while models.SessionKey.objects.filter(session_key=session_key).exists():
                    time.sleep(0.001)
                    session_key = models.SessionKey.generate_key(email=email)
                models.SessionKey.objects.create(user=user, key=session_key)
            else:
                session_key = models.SessionKey.objects.get(user=user).key
            return JsonResponse(data={'success': True, 'sessionKey': session_key})
        else:
            return JsonResponse(data={'success': False})
    else:
        return JsonResponse(data={'success': False, 'reason': 'bad params, must provide email and password'})


# endregion


# region settings
@require_http_methods(['POST'])
def handle_fetch_settings_api(request):
    if 'sessionKey' in request.POST:
        session_key = request.POST['sessionKey']
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user
            if wn_models.Preferences.objects.filter(user=user).exists():
                preferences = wn_models.Preferences.objects.get(user=user)
                return JsonResponse(data={
                    'success': True,
                    'name': preferences.name,
                    'date_of_birth': preferences.date_of_birth,
                    'gender': preferences.gender,
                    'is_profile_shared': preferences.shared_profile,
                })
            else:
                return JsonResponse(data={'success': False, 'reason': 'no settings associated with user, please contact the developer'})
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': 'bad params, must provide sessionKey'})


@require_http_methods(['POST'])
def handle_update_settings_api(request):
    if 'sessionKey' in request.POST:
        session_key = request.POST['sessionKey']
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user
            if wn_models.Preferences.objects.filter(user=user).exists():
                preferences = wn_models.Preferences.objects.get(user=user)
                if 'name' in request.POST:
                    preferences.name = request.POST['name']
                if 'date_of_birth' in request.POST:
                    preferences.date_of_birth = request.POST['date_of_birth']
                if 'gender' in request.POST:
                    preferences.gender = request.POST['gender']
                if 'is_profile_shared' in request.POST:
                    preferences.shared_profile = request.POST['is_profile_shared']
                return JsonResponse(data={'success': True})
            else:
                return JsonResponse(data={'success': False, 'reason': 'no settings associated with user, please contact the developer'})
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': 'bad params, must provide sessionKey'})


# endregion


# region exercises & body parts
@require_http_methods(['POST'])
def handle_fetch_exercises_api(request):
    exercises = wn_models.Exercise.objects.all()
    exercises_arr = []
    for exercise in exercises:
        exercises_arr += [{
            'id': exercise.id,
            'name': exercise.name,
            'body_part_str': exercise.body_part.name,
            'category_str': exercise.category.name,
            'icon_str': exercise.icon,
        }]
    return JsonResponse(data={
        'success': True,
        'exercises': exercises_arr
    })


@require_http_methods(['POST'])
def handle_fetch_body_parts_api(request):
    body_parts = wn_models.BodyPart.objects.all()
    body_parts_arr = []
    for body_part in body_parts:
        body_parts_arr += [{
            'id': body_part.id,
            'name': body_part.name,
        }]
    return JsonResponse(data={
        'success': True,
        'body_parts': body_parts_arr
    })


# endregion


# region workout
@require_http_methods(['POST'])
def handle_insert_workout_api(request):
    required_params = ['title', 'timestamp', 'duration']
    if False not in [x in request.POST for x in required_params]:
        session_key = request.POST['sessionKey']
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user
            workout_session = wn_models.WorkoutSession.objects.create(
                user=user,
                timestamp=int(request.POST['timestamp']),
                title=request.POST['title'],
                duration=int(request.POST['duration']),
            )
            return JsonResponse(data={
                'success': True,
                'workout_session': {
                    'id': workout_session.id,
                    'title': workout_session.title,
                    'timestamp': int(workout_session.timestamp.timestamp() * 1000),
                    'duration': workout_session.duration,
                }
            })
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})


def handle_fetch_workouts_api(request):
    required_params = ['sessionKey', 'dateTimestampMs']
    if False not in [x in request.POST for x in required_params]:
        session_key = request.POST['sessionKey']
        date = datetime.utcfromtimestamp(t=int(request.POST['dateTimestampMs']) / 1000)
        date_from_ts = date.replace(day=0, hour=0, minute=0, second=0, microsecond=0).timestamp()
        date_till_ts = (date.replace(day=0, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).timestamp()
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user
            workout_sessions = []
            for workout_session in wn_models.WorkoutSession.objects.filter(user=user, timestamp__gte=date_from_ts, timestamp__lt=date_till_ts):
                lifts = []
                for lift in wn_models.Lift.objects.filter(workout_session=workout_session):
                    lifts += [{
                        'id': lift.id,
                        'timestamp': int(lift.timestamp.timestamp() * 1000),
                        'one_rep_max': lift.one_rep_max,
                        'exercise_id': lift.exercise.id,
                        'exercise_name': lift.exercise.name,
                        'lift_mass': lift.lift_mass,
                        'repetitions': lift.repetitions,
                    }]
                workout_sessions += [
                    {
                        'id': workout_session.id,
                        'title': workout_session.title,
                        'timestamp': int(workout_session.timestamp.timestamp() * 1000),
                        'duration': workout_session.duration,
                        'lifts': lifts
                    }
                ]
            return JsonResponse(data={
                'success': True,
                'workouts': workout_sessions
            })
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})


# endregion


# region lifts
@require_http_methods(['POST'])
def handle_insert_lift_api(request):
    required_params = ['sessionKey', 'timestamp', 'lift_mass', 'exercise_id', 'workout_session_id']
    if False not in [x in request.POST for x in required_params]:
        session_key = request.POST['sessionKey']
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user

            if wn_models.Exercise.objects.filter(name=request.POST['exercise_id']).exists() and wn_models.WorkoutSession.objects.filter(id=int(request.POST['workout_session_id'])).exists():
                exercise = wn_models.Exercise.objects.filter(name=request.POST['exercise_id'])
                workout_session = wn_models.WorkoutSession.objects.get(id=int(request.POST['workout_session_id']))
                lift = wn_models.Lift.objects.create(
                    timestamp=int(request.POST['timestamp']),
                    workout_session=workout_session,
                    exercise=exercise,
                    lift_mass=float(request.POST['lift_mass']),
                    repetitions=float(request.POST['repetitions']),
                    one_rep_max=float(request.POST['one_rep_max']),
                )
                return JsonResponse(data={
                    'success': True,
                    'lift': {
                        'id': lift.id,
                        'timestamp': int(lift.timestamp.timestamp() * 1000),
                        'exercise_id': lift.exercise.id,
                        'exercise_name': lift.exercise.name,
                        'workout_session_id': lift.workout_session.id,
                        'lift_mass': lift.workout_session.lift_mass,
                        'repetitions': lift.workout_session.repetitions,
                        'one_rep_max': lift.workout_session.one_rep_max,
                    }
                })
            else:
                return JsonResponse(data={'success': False, 'reason': 'double check workout_session_id and exercise_id'})
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
# endregion