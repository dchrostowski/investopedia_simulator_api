import puppeteer from "puppeteer";
import fs from "fs";


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

        await page.goto(link, {waitUntil:'load',timeout: 10000})
        //await page.waitForXPath('//span[contains(text(),"LOG IN")]', {timeout: 3000})
        const loginButton = await page.waitForSelector('::-p-xpath(//span[contains(text(),"LOG IN")])', {timeout: 3000})

        const cookies1 = await page.cookies()
        //console.log(cookies1)
        
        console.log(loginButton)
        await loginButton.click()

        const usernameField = await page.waitForSelector('::-p-xpath(//input[@id="username"])', {timeout: 3000})
        const passwordField = await page.waitForSelector('::-p-xpath(//input[@id="password"])', {timeout: 3000})
        const signInButton = await page.waitForSelector('::-p-xpath(//input[@id="login"])', {timeout: 3000})

        const cookies2 = await page.cookies()
        //console.log("cookies2:")
        //console.log(cookies2)

        console.log(usernameField)
        console.log(passwordField)

        await usernameField.type(username)
        

        
        await passwordField.type(password)
        

        await signInButton.click()
        await waitFor(3000)

        const passwordField2 = await page.waitForSelector('::-p-xpath(//input[@id="password"])', {timeout: 3000})
        passwordField2.type(password)

        page.on('request', request => {
            const url = request.url()
            if(url === 'https://api.investopedia.com/simulator/graphql' && authHeader === null) {
                const requestHeaders = request.headers()
                if(requestHeaders?.authorization) {
                    authHeader = {'Authorization': requestHeaders['authorization']}
                    console.log("successfully extracted auth token.")
                    fs.writeFileSync(`./auth.json`, JSON.stringify(authHeader))
                }
                
            }
        })

        const signInButton2 = await page.waitForSelector('::-p-xpath(//input[@id="login"])', {timeout: 3000})
        await signInButton2.click()

        
        




        //await page.waitForSelector('::-p-xpath(//span[@class="v-btn__content"])', {timeout:10000})

        // await page.screenshot({'path':'./ss2.png'})



        // const text = await page.evaluate(el => el.textContent, elHandle[0])
        // console.log(`got score: ${text} `)
        // const score = text.trim().replace('/100','')
        // const balancesheetScore = await pullScore(page, "Financial Strength")
        // const profitabilityScore = await pullScore(page, "Profitability Rank")
        // const growthScore = await pullScore(page, "Growth Rank")
        // const valueScore = await pullScore(page, "GF Value Rank")
        // const momentumScore = await pullScore(page, "Momentum Rank")


        // const priceEl = await page.$x('//div[@class="m-t-xs"]/span[1]')
        // const priceText = await page.evaluate(el => el.textContent, priceEl[0])
        // const price = priceText.trim().replace('$','').trim()

        // console.log(`Data for ${symbol}:`)
        // const item = {
        //     'symbol': symbol,
        //     'price_at_rating': price,
        //     'balancesheet': balancesheetScore,
        //     'profitability': profitabilityScore,
        //     'growth': growthScore,
        //     'value': valueScore,
        //     'momentum': momentumScore,
        //     'quant': score
        // }


        // console.log(item)
        // fs.writeFileSync(`gurufocus_${symbol}.json`, JSON.stringify(item))

    }
    catch(err) {
        console.error(err)
    }

    finally {
        await page.close()
        await browser.close();
        process.exit(0)
    }

  })();

