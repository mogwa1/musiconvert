#include "mainwindow.h"
#include <QApplication>
#include <QDebug>

int main(int argc, char *argv[])
{
    //QIcon::setThemeName( "breeze" );
    //qDebug() << QIcon::themeSearchPaths();
    QApplication a(argc, argv);
    MainWindow w;
    w.show();

    return a.exec();
}
