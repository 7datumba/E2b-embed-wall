import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
const server=spawn(process.execPath,['terminal-server.mjs'],{stdio:['ignore','pipe','pipe']});
let browser,ff;
try{
 await new Promise((resolve,reject)=>{server.on('error',reject);server.on('exit',c=>reject(Error('terminal server exited '+c)));const deadline=Date.now()+10000;const check=async()=>{try{const r=await fetch('http://127.0.0.1:8877/done');if(r.ok)return resolve()}catch{}if(Date.now()>deadline)return reject(Error('server startup timeout'));setTimeout(check,100)};check()});
 browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:false,args:['--no-sandbox','--window-size=1280,810','--window-position=0,0','--force-device-scale-factor=1']});
 const page=await browser.newPage({viewport:{width:1280,height:720}});
 await page.goto('http://127.0.0.1:8877/');await page.waitForFunction(()=>window.term);
 await page.mouse.move(1275,1);await page.screenshot({path:'/downloads/terminal-v6-start.png'});
 ff=spawn('ffmpeg',['-y','-f','x11grab','-video_size','1280x720','-framerate','30','-i',process.env.DISPLAY+'+0,87','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','/downloads/e2b-bounded-open-weights-raw.mp4']);
 await new Promise((resolve,reject)=>{ff.on('error',reject);ff.on('exit',c=>reject(Error('ffmpeg exited '+c)));ff.stderr.on('data',d=>{if(d.toString().includes('frame='))resolve()});setTimeout(()=>reject(Error('screen capture did not start')),8000)});ff.stderr.on('data',()=>{});
 await page.evaluate(()=>fetch('/start'));
 let outcome;const deadline=Date.now()+2400000;while(true){outcome=await(await fetch('http://127.0.0.1:8877/done')).json();if(outcome.done===true)break;if(Date.now()>deadline)throw Error('Measurement timeout');await new Promise(r=>setTimeout(r,200));}
 await new Promise(r=>setTimeout(r,2500));await page.screenshot({path:'/downloads/terminal-v6-end.png'});
 ff.stdin.write('q');await new Promise(r=>ff.on('exit',r));ff=null;
 if(outcome.exitCode!==0)throw Error('Live measurement failed, exit '+outcome.exitCode);
 console.log('Live capture saved. Measurement process exited 0.');
}finally{if(ff&&ff.exitCode===null){ff.stdin.write('q');await new Promise(r=>ff.on('exit',r))}if(browser)await browser.close();server.kill();}
