"use strict";
module.exports={
  testDir:__dirname,
  testMatch:"*.spec.js",
  timeout:30000,
  expect:{timeout:10000},
  use:{baseURL:"http://127.0.0.1:8765",trace:"retain-on-failure",screenshot:"only-on-failure"},
  projects:[
    {name:"desktop-chromium",use:{browserName:"chromium",viewport:{width:1365,height:768}}},
    {name:"mobile-webkit",use:{browserName:"webkit",viewport:{width:390,height:844},deviceScaleFactor:3,isMobile:true,hasTouch:true}}
  ],
  webServer:{command:"python3 -m http.server 8765 --bind 127.0.0.1 --directory preview-v18-7",port:8765,reuseExistingServer:false,timeout:30000}
};
