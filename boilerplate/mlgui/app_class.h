#pragma once
#include "mlgui.2/src/App.h"

class MainWindow;
class **ClassApp** : public ml::App
{
    public:
        **ClassApp**(int argc, char *argv[]);
        virtual ~**ClassApp**();
        void initProps();
        void createWindows();
        void setEvents();

    private : 
        MainWindow* _**classapp**W=nullptr;
};

namespace **classapp**
{
    **ClassApp*** get();
}
