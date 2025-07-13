
from django.db.models import  Count, Avg
from django.shortcuts import render, redirect
from django.db.models import Count
from django.db.models import Q
import datetime
import xlwt
from django.http import HttpResponse


import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

# Create your views here.
from Remote_User.models import ClientRegister_Model,prediction_bus_boarding,detection_ratio,detection_accuracy


def serviceproviderlogin(request):
    if request.method  == "POST":
        admin = request.POST.get('username')
        password = request.POST.get('password')
        if admin == "Admin" and password =="Admin":
            detection_accuracy.objects.all().delete()
            return redirect('View_Remote_Users')

    return render(request,'SProvider/serviceproviderlogin.html')

def View_Predicted_Hourly_Boarding_Demand_Type_Ratio(request):
    detection_ratio.objects.all().delete()
    ratio = ""
    kword = 'Less Demand'
    print(kword)
    obj = prediction_bus_boarding.objects.all().filter(Q(Prediction=kword))
    obj1 = prediction_bus_boarding.objects.all()
    count = obj.count();
    count1 = obj1.count();
    ratio = (count / count1) * 100
    if ratio != 0:
        detection_ratio.objects.create(names=kword, ratio=ratio)

    ratio12 = ""
    kword12 = 'More Demand'
    print(kword12)
    obj12 = prediction_bus_boarding.objects.all().filter(Q(Prediction=kword12))
    obj112 = prediction_bus_boarding.objects.all()
    count12 = obj12.count();
    count112 = obj112.count();
    ratio12 = (count12 / count112) * 100
    if ratio12 != 0:
        detection_ratio.objects.create(names=kword12, ratio=ratio12)


    obj = detection_ratio.objects.all()
    return render(request, 'SProvider/View_Predicted_Hourly_Boarding_Demand_Type_Ratio.html', {'objs': obj})

def View_Remote_Users(request):
    obj=ClientRegister_Model.objects.all()
    return render(request,'SProvider/View_Remote_Users.html',{'objects':obj})

def charts(request,chart_type):
    chart1 = detection_ratio.objects.values('names').annotate(dcount=Avg('ratio'))
    return render(request,"SProvider/charts.html", {'form':chart1, 'chart_type':chart_type})

def charts1(request,chart_type):
    chart1 = detection_accuracy.objects.values('names').annotate(dcount=Avg('ratio'))
    return render(request,"SProvider/charts1.html", {'form':chart1, 'chart_type':chart_type})

def View_Predicted_Hourly_Boarding_Demand_Type(request):
    obj =prediction_bus_boarding.objects.all()
    return render(request, 'SProvider/View_Predicted_Hourly_Boarding_Demand_Type.html', {'list_objects': obj})

def likeschart(request,like_chart):
    charts =detection_accuracy.objects.values('names').annotate(dcount=Avg('ratio'))
    return render(request,"SProvider/likeschart.html", {'form':charts, 'like_chart':like_chart})


def Download_Trained_DataSets(request):

    response = HttpResponse(content_type='application/ms-excel')
    # decide file name
    response['Content-Disposition'] = 'attachment; filename="Predicted_Datasets.xls"'
    # creating workbook
    wb = xlwt.Workbook(encoding='utf-8')
    # adding sheet
    ws = wb.add_sheet("sheet1")
    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    # headers are bold
    font_style.font.bold = True
    # writer = csv.writer(response)
    obj = prediction_bus_boarding.objects.all()
    data = obj  # dummy method to fetch data.
    for my_row in data:
        row_num = row_num + 1
        ws.write(row_num, 0, my_row.Fid, font_style)
        ws.write(row_num, 1, my_row.TripID, font_style)
        ws.write(row_num, 2, my_row.RouteID, font_style)
        ws.write(row_num, 3, my_row.StopID, font_style)
        ws.write(row_num, 4, my_row.StopName, font_style)
        ws.write(row_num, 5, my_row.WeekBeginning, font_style)
        ws.write(row_num, 6, my_row.NumberOfBoardings, font_style)
        ws.write(row_num, 7, my_row.Prediction, font_style)

    wb.save(response)
    return response

def train_model(request):
    detection_accuracy.objects.all().delete()
    prediction_bus_boarding.objects.all().delete()

    df = pd.read_csv('Datasets.csv')

    def apply_response(Label):
        if Label == 0:
            return 0  # Less Demand
        elif Label == 1:
            return 1  # More Demand

    df['results'] = df['Label'].apply(apply_response)

    cv = CountVectorizer()
    X = df['Fid']
    y = df['results']

    X = cv.fit_transform(X)

    models = []
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20)

    # 1. Deep Neural Network (MLPClassifier)
    from sklearn.neural_network import MLPClassifier
    mlpc = MLPClassifier().fit(X_train, y_train)
    y_pred = mlpc.predict(X_test)
    detection_accuracy.objects.create(names="Deep Neural Network-DNN", ratio=accuracy_score(y_test, y_pred) * 100)
    models.append(('MLPClassifier', mlpc))

    # 2. SVM
    from sklearn import svm
    lin_clf = svm.LinearSVC()
    lin_clf.fit(X_train, y_train)
    predict_svm = lin_clf.predict(X_test)
    detection_accuracy.objects.create(names="SVM", ratio=accuracy_score(y_test, predict_svm) * 100)
    models.append(('SVM', lin_clf))

    # 3. Logistic Regression
    from sklearn.linear_model import LogisticRegression
    reg = LogisticRegression(random_state=0, solver='lbfgs')
    reg.fit(X_train, y_train)
    y_pred_logistic = reg.predict(X_test)
    detection_accuracy.objects.create(names="Logistic Regression", ratio=accuracy_score(y_test, y_pred_logistic) * 100)
    models.append(('Logistic', reg))

    # 4. Gradient Boosting Classifier
    from sklearn.ensemble import GradientBoostingClassifier
    clf = GradientBoostingClassifier(n_estimators=100, learning_rate=1.0, max_depth=1, random_state=0)
    clf.fit(X_train, y_train)
    clfpredict = clf.predict(X_test)
    detection_accuracy.objects.create(names="Gradient Boosting Classifier", ratio=accuracy_score(y_test, clfpredict) * 100)
    models.append(('GradientBoostingClassifier', clf))

    # Predict on full dataset using Logistic Regression and store results
    X_full = cv.transform(df['Fid'])
    df['Prediction'] = reg.predict(X_full)

    for i, row in df.iterrows():
        prediction_bus_boarding.objects.create(
            Fid=row['Fid'],
            TripID=row['TripID'],
            RouteID=row['RouteID'],
            StopID=row['StopID'],
            StopName=row['StopName'],
            WeekBeginning=row['WeekBeginning'],
            NumberOfBoardings=row['NumberOfBoardings'],
            Prediction='More Demand' if row['Prediction'] == 1 else 'Less Demand'
        )

    obj = detection_accuracy.objects.all()
    return render(request, 'SProvider/train_model.html', {'objs': obj})
