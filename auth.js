import puppeteer from "puppeteer";
import fs from "fs";

let fileWritten = false
const waitFor = async (timeToWait) => {

    return new Promise(resolve => {
        setTimeout(() => {
            return resolve()
        },timeToWait)
    })

}



(async () => {
    //const links = JSON.parse(await fs.readFileSync('../gurufocus_unscrapable.json'))
    if(process.argv.length !== 4) {
        console.error("invalid arguments.")
        process.exit(1)
    }
    const username = process.argv[2]
    const password = process.argv[3]
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    const link = 'https://investopedia.com/simulator'

    try {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        await page.setViewport({width: 1366, height: 768});
        await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36');
        let authHeader = null

        page.on('response', async response => {
            if(response.url() === 'https://www.investopedia.com/auth/realms/investopedia/protocol/openid-connect/token') {
                const response_json = await response.json()
                fs.writeFileSync('./auth.json',JSON.stringify(response_json))
                fileWritten = true
            }
        })

        await page.goto(link, {waitUntil:'load',timeout: 15000})
        //await page.waitForXPath('//span[contains(text(),"LOG IN")]', {timeout: 3000})
        const loginButton = await page.waitForSelector('::-p-xpath(//span[contains(text(),"LOG IN")])', {timeout: 3000})
        
        await loginButton.click()
	    await waitFor(6000)

        const usernameField = await page.waitForSelector('::-p-xpath(//input[@id="username"])', {timeout: 3000})
        const passwordField = await page.waitForSelector('::-p-xpath(//input[@id="password"])', {timeout: 3000})
        const signInButton = await page.waitForSelector('::-p-xpath(//input[@id="login"])', {timeout: 3000})


        await usernameField.type(username)
        await passwordField.type(password)

        await waitFor(6000)
        

        await signInButton.click()

        await waitFor(6000)
        await page.screenshot()

        const passwordField2 = await page.waitForSelector('::-p-xpath(//input[@id="password"])', {timeout: 3000})
        passwordField2.type(password)

        await page.screenshot()

        // page.on('request', request => {
        //     const url = request.url()
        //     if(url === 'https://api.investopedia.com/simulator/graphql' && authHeader === null) {
        //         const requestHeaders = request.headers()
        //         if(requestHeaders?.authorization) {
        //             authHeader = {'Authorization': requestHeaders['authorization']}
        //             console.log("successfully extracted auth token.")
        //             fs.writeFileSync(`./auth.json`, JSON.stringify(authHeader))
        //         }
                
        //     }
        // })

       

        const signInButton2 = await page.waitForSelector('::-p-xpath(//input[@id="login"])', {timeout: 3000})
        await signInButton2.click()
	    await page.screenshot()
        
        await page.waitForSelector('::-p-xpath(//div[contains(@class,"v-main__wrap")])')

    }
    catch(err) {
        if(!fileWritten) {
            console.error(err)
        }
        
    }

    finally {
        await page.close()
        await browser.close();
        if(fileWritten) {
            console.log("login successful")
        }
        process.exit(0)
    }

  })();
