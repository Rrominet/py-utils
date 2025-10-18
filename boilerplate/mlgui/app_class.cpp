#include "./**ClassApp**.h"
#include "./MainWindow.h"
#include "mlgui.2/src/App.hpp"
namespace **classapp**
{
    **ClassApp*** _**classapp** = nullptr;
}

**ClassApp**::**ClassApp**(int argc,char *argv[]) : ml::App(argc,argv)
{
    **classapp**::_**classapp** = this;	
    this->initProps();
    this->createWindows();
    this->setEvents();
    this->addCss("**classapp**.css");
}

void **ClassApp**::setEvents()
{

}

void **ClassApp**::initProps()
{

}

void **ClassApp**::createWindows()
{

}

**ClassApp**::~**ClassApp**()
{
    **classapp**::_**classapp** = nullptr;	
}

namespace **classapp**
{
    **ClassApp*** get(){return _**classapp**;}
}

