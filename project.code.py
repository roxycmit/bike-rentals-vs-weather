from pathlib import Path
#path lets us build file locations that work on any computer
import numpy as np
#numpy uses an array of numbers
import matplotlib.pyplot as plt
#matplotlib draws the figure

#list the settings that they are easy to locate and change if necessary

#__file__ is the location of this script
#resolve() gives the absolute path, and parent gives the folder containing the file
BASE = Path(__file__).resolve().parent
#the / joins the folder with the filename, so this works on any computer
DATA_FILE = BASE / "data.py.csv"
#figure file is saved in the same folder as the script
FIGURE_FILE = BASE / "bike_results.png"

#part 4 will split the days into 10 subsamples, so we can estimate the uncertainty on the slope
N_SUBSAMPLES = 10
#part 3 will average the rentals in temperature bins of 5 degrees, starting at 0 degrees celsius and stopping before 45 degrees
#bin width 5 was chosen because too narrow bins will contain too few days which we are already avoiding by ignoring bins with fewer than 5 days, and too wide bins will average over too large a temperature range
TEMPERATURE_BINS = np.arange(0, 45, 5)
#ignore bins with fewer than 5 days because the average and spread of so few days are not reliable, and it keeps the plot clearer
MIN_DAYS_PER_BIN = 5

#Weather codes in the dataset are 1, 2 and 3, so we can store the names in a dictionary for easy lookup
WEATHER_NAMES = {
    1: "Clear / partly cloudy",
    2: "Mist / cloudy",
    3: "Light rain / snow",
}

#functions to help with the analysis

def mean_and_error(values):
    #Average of the values and its uncertainty, which is the standard deviation (SD)
    #Uncertainty = standard deviation = how much a single value (for example one day) typically differs from the average
        #does not get smaller with more days: it describes the spread of the data, not how precisely the average is known
    #(ddof=1 gives the sample standard deviation, as in the homework)
    mean = np.mean(values)
    error = np.std(values, ddof=1)
    return mean, error


def load_data():
    #Read the numeric columns we need from the csv file and return them as arrays. The first row of the csv file is a header, so skip it
    #Column numbers in data.py.csv, counting from 0:
    #3 = yr (0: 2011, 1: 2012), 8 = weathersit (1 clear, 2 mist/cloudy, 3 rain/snow),
    #9 = temp (scaled), 15 = cnt (total rentals that day)
    #np.loadtxt() reads the data into a 2D array, where each row is a day and each column is one of the columns we read
    #delimiter="," tells it that the columns are separated by commas, 
    #skiprows=1 skips the header row
    #usecols=(3, 8, 9, 15) reads only those columns
    data = np.loadtxt(DATA_FILE, delimiter=",", skiprows=1, usecols=(3, 8, 9, 15))
    #data[:, 0] is the first column (year) and all rows
    year = data[:, 0]
    #data[:, 1] is the second column (weather) and all rows
    #astype(int) converts the weather codes from float to int, so we can use them as dictionary keys (1.0 into 1)
    weather = data[:, 1].astype(int)
    #The dataset stores temperature divided by 41, so multiply to get degrees Celsius
    temperature = 41 * data[:, 2]

    #fourth column is the number of rentals that day
    rentals = data[:, 3]

    #this is to check that we read the data correctly, and to give a sense of the size of the dataset
    #is not necessary for the analysis, but is useful for debugging
    #counts should match the number of rows in the dataset, and the first 5 values should match the first 5 rows of the dataset
    print("Number of days:", len(rentals))
    print("Number of temperatures:", len(temperature))
    print("First 5 temperatures:", temperature[:5])
    print("First 5 rentals:", rentals[:5])

    #return the arrays so they can be used in the exercises
    return year, weather, temperature, rentals

#Part 1: mean rentals for each weather type

def part1(weather, rentals):
    print("Part 1: Mean rentals per day for each weather type")

    #Dictionaries that store the results for weather code 1, 2 and 3
    #for example, weather_means[1] is the mean rentals for clear days, weather_errors[2] is the uncertainty (standard deviation) for misty days, and weather_days[3] is the number of rainy days
    weather_means = {}
    weather_errors = {}
    weather_days = {}

    #repeat the analysis for each weather code
    for code in [1, 2, 3]:
        #weather == code creates a boolean array that is True for days with this weather code and False for other days, only the True days are selected from rentals
        values = rentals[weather == code]
        #mean_and_error(values) returns the mean and the uncertainty (standard deviation) for this weather code
        mean, error = mean_and_error(values)
        #store the results in the dictionaries for other parts and for the plot
        weather_means[code] = mean
        weather_errors[code] = error
        #store the number of days with this weather code, which is the length of the values array
        weather_days[code] = len(values)
        #print the results in a formatted way, with the weather name, number of days, mean rentals and uncertainty (standard deviation) - f-strings puts numbers into text
        #24s=24 characters wide
        #3d=3 digits wide
        #7.1f=7 characters wide, 1 decimal place
        print(f"  {WEATHER_NAMES[code]:24s} N = {len(values):3d}  "
              f"mean = {mean:7.1f} +/- {error:.1f}")

    #print a blank line to separate the output from the next part
    print()
    #give the results to the next part  and to the plot
    return weather_means, weather_errors, weather_days

#Part 2: difference between clear and rainy days

def part2(weather_means, weather_errors):
    print("Part 2: Difference between clear days and rainy days")

    #For two independent numbers the uncertainty of the difference is sqrt(error_1^2 + error_2^2)
    #uncertainty on the difference is the quadrature sum of the two standard deviations, so it describes the spread of the difference between one clear day and one rainy day
    #clear days are weather code 1, rainy/snowy days are weather code 3
    difference = weather_means[1] - weather_means[3]
    #uncertainty of that difference
    difference_error = np.sqrt(weather_errors[1] ** 2 + weather_errors[3] ** 2)
    #how much percent fewer rentals on rainy days compared to clear days, as a percentage of the clear day mean
    percent_fewer = 100 * (1 - weather_means[3] / weather_means[1])

    #print the results in a formatted way, with the difference, uncertainty and percentage fewer rentals on rainy days
    #.0f=0 decimal places
    print(f"  Clear minus rain/snow: {difference:.0f} +/- {difference_error:.0f} "
          f"rentals per day ({percent_fewer:.0f}% fewer on rainy days)")
    print()

#Part 3: rentals as a function of temperature

def part3(temperature, rentals):
    print("Part 3: Rentals as a function of temperature")

    #Average the rentals in temperature bins of 5 degrees
    #create empty lists to store the bin centres, means and errors for each bin
    bin_centres = []
    bin_means = []
    bin_errors = []

    #Loop over the temperature bins, using zip to pair the low and high edges of each bin
    #each loop iteration gives the low and high edges of one bin, for example 0 and 5, then 5 and 10, etc.
    for low, high in zip(TEMPERATURE_BINS[:-1], TEMPERATURE_BINS[1:]):
        #true for days with temperature in this bin, false for other days
        in_bin = (temperature >= low) & (temperature < high)
        #np.sum(in_bin) counts the number of days in this bin (true values)
        if np.sum(in_bin) < MIN_DAYS_PER_BIN:
            #if it is less than MIN_DAYS_PER_BIN, skip this bin using continue, which goes to the next iteration of the loop
            continue
        #mean_and_error(rentals[in_bin]) returns the mean and the uncertainty (standard deviation) for this bin, using only the days in this bin
        mean, error = mean_and_error(rentals[in_bin])
        #store the bin centre(x position in plot), mean and error in the lists for the plot
        bin_centres.append((low + high) / 2)
        bin_means.append(mean)
        bin_errors.append(error)
        #print one line per bin, with the bin edges, number of days, mean rentals and uncertainty (standard deviation)
        print(f"  {low:2d}-{high:2d} C  N = {np.sum(in_bin):3d}  "
              f"mean = {mean:7.1f} +/- {error:.1f}")

    #Straight-line fit through all days: rentals = slope * temperature + intercept
    #np.polyfit() returns the slope and intercept of the best-fit line through the data, using a least-squares fit
    slope, intercept = np.polyfit(temperature, rentals, 1)
    #np.corrcoef() returns the correlation matrix, which is a 2x2 array with the correlation coefficients between the two variables. The correlation coefficient r is in the [0, 1] position of the matrix.
    correlation = np.corrcoef(temperature, rentals)[0, 1]
    print(f"  Straight-line fit: slope = {slope:.1f} rentals per day per degree C, "
          f"correlation r = {correlation:.2f}")

    print()
    #give back results for the plot and for the next part
    return bin_centres, bin_means, bin_errors, slope, intercept

#Part 4: uncertainty on the slope with sub-sampling

def part4(temperature, rentals):
    print("Part 4: Uncertainty on the slope with sub-sampling")

    #Shuffle the days randomly, split them into 10 subsamples, fit the slope in each one
    #The average slope and its standard deviation come from the 10 subsample slopes
    #fixed random seed so the result is reproducible, so that the same random numbers are generated each time the code is run
    np.random.seed(42)
    #np.random.permutation() returns a random permutation of the indices of the days, which is an array of integers from 0 to len(rentals)-1 (730)in random order
    shuffled_days = np.random.permutation(len(rentals))
    #np.array_split() splits the shuffled days into N_SUBSAMPLES equal parts, which is a list of arrays of indices of about 73 days each for each subsample
    subsample_days = np.array_split(shuffled_days, N_SUBSAMPLES)

    #Fit each subsample and store the slopes in a list
    subsample_slopes = []
    for days in subsample_days:
        #straight-line fit through the subsample days, using only the days in this subsample
        #[0] gets the slope from the array returned by np.polyfit(), which is [slope, intercept]
        subsample_slope = np.polyfit(temperature[days], rentals[days], 1)[0]
        subsample_slopes.append(subsample_slope)

    #treat the 10 subsample slopes as 10 measurements of the slope, and calculate their mean and standard deviation
    slope_mean, slope_error = mean_and_error(subsample_slopes)
    print(f"  Sub-sampling ({N_SUBSAMPLES} subsamples): slope = {slope_mean:.1f} "
          f"+/- {slope_error:.1f} rentals per day per degree C")

    print()
    return slope_mean, slope_error

#Part 5: check whether the weather effect shows up in each year separately, because rentals grew a lot from 2011 to 2012

def part5(year, weather, temperature, rentals):
    print("Part 5: Year-by-year check")

    #Rentals grew a lot from 2011 to 2012, which also affects the comparisons above
    #we repeat the analysis inside each year to see if the weather effect is still there when the years are not mixed:
    #the slope of rentals vs temperature, and the difference between clear and rainy days
    #compare the mean rentals per day in 2011 and 2012, and the uncertainty (standard deviation)
    mean_2011, error_2011 = mean_and_error(rentals[year == 0])
    mean_2012, error_2012 = mean_and_error(rentals[year == 1])
    print(f"  Mean rentals per day: 2011 = {mean_2011:.0f} +/- {error_2011:.0f}, "
          f"2012 = {mean_2012:.0f} +/- {error_2012:.0f}")

    #check whether the temperature-rental relationship is similar in both years
    for y in [0, 1]:
        #Select only the days from this year
        days = year == y

        #Calculate the temperature-rental slope for this year
        slope, intercept = np.polyfit(
            temperature[days],
            rentals[days],
            1
        )

        #Calculate correlation between rentals and temperature for this year
        correlation = np.corrcoef(
            temperature[days],
            rentals[days]
        )[0, 1]

        #convert year code (0 or 1) to actual year number (2011 or 2012)
        year_number = 2011 + y

        print(f"  {year_number}: slope = {slope:.1f}, "
              f"correlation r = {correlation:.2f}")

        #difference between clear days and rainy days inside this year, same method as part 2
        #weather == 1 are clear days, weather == 3 are rain/snow days; "&" keeps only days that satisfy both conditions
        clear_mean, clear_error = mean_and_error(rentals[days & (weather == 1)])
        rain_mean, rain_error = mean_and_error(rentals[days & (weather == 3)])
        difference = clear_mean - rain_mean
        difference_error = np.sqrt(clear_error ** 2 + rain_error ** 2)
        percent_fewer = 100 * (1 - rain_mean / clear_mean)
        #number of rain/snow days this year (very few in 2012, so that result is less reliable)
        rain_days = np.sum(days & (weather == 3))
        print(f"  {year_number}: clear minus rain/snow = {difference:.0f} +/- {difference_error:.0f} "
              f"({percent_fewer:.0f}% fewer, {rain_days} rain/snow days)")

    print()

#Part 6: plot (left = temperature, right = weather type)

def part6(temperature, rentals, weather_means, weather_errors, weather_days,
              bin_centres, bin_means, bin_errors, slope, intercept):
    print("Part 6: Plot of the results")

    #Create a figure with two subplots, one for the temperature analysis and one for the weather type analysis
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.5))

    #Left: every day as a gray dot, the bin averages with error bars, and the fit
    #dots plotted with s=10 (size) and color="lightgray" for clarity, label is used for the legend
    #x=temperature, y=rentals, s=size of dots, color=color of dots, label=label for legend
    left.scatter(temperature, rentals, s=10, color="lightgray", label="Single days")
    #bin averages as black dots with error bars, fmt="o" means circle markers, capsize=3 means the error bars have caps of 3 points, label is used for the legend
    left.errorbar(bin_centres, bin_means, yerr=bin_errors, fmt="o", color="black",
                  capsize=3, label="Mean per 5 C bin (+/- std)")
    #100 points between the minimum and maximum temperature for the fit line, to make it smooth
    fit_x = np.linspace(temperature.min(), temperature.max(), 100)
    #plot the fit line in red, with the slope and intercept from the straight-line fit, and a label for the legend that shows the slope rounded to 0 decimal places
    left.plot(fit_x, slope * fit_x + intercept, color="red",
              label=f"Fit: {slope:.0f} rentals per C")
    left.set_xlabel("Temperature (C)")
    left.set_ylabel("Rentals per day")
    left.set_title("Rentals as a function of temperature")
    left.grid(True)
    left.legend()

    #Right: mean rentals for each weather type with the uncertainty (standard deviation)
    codes = [1, 2, 3]
    #x positions are 0, 1, 2 for the three weather types, y values are the means, yerr values are the uncertainties (standard deviations)
    #collect the means and uncertainties from the dictionaries using a list comprehension
    right.errorbar(
        range(3),
        [weather_means[c] for c in codes],
        yerr=[weather_errors[c] for c in codes],
        fmt="o", color="black", capsize=5,
    )
    #put a tick for each weather type, and label it with the weather name and the number of days in that category
    right.set_xticks(range(3))
    right.set_xticklabels([f"{WEATHER_NAMES[c]}\nN = {weather_days[c]}" for c in codes],
                          fontsize=8)
    right.set_xlim(-0.5, 2.5)
    right.set_ylim(bottom=0)
    right.set_ylabel("Mean rentals per day (+/- std)")
    right.set_title("Rentals for each weather type")
    right.grid(True)

    #adjust spacing so labels do not overlap
    fig.tight_layout()
    #save the figure to a file (dpi=150 is high resolution)
    fig.savefig(FIGURE_FILE, dpi=150)
    print(f"  Figure saved to {FIGURE_FILE}")
    #show the figure on the screen, which is useful for interactive use but not necessary for automated testing
    plt.show()

#Run all parts

def main():
    #Load the data and print the number of days and mean rentals per day
    year, weather, temperature, rentals = load_data()
    print(f"Loaded {len(rentals)} days, mean = {np.mean(rentals):.0f} rentals per day\n")

    #Run each part of the analysis in order, passing the necessary data and results between them
    weather_means, weather_errors, weather_days = part1(weather, rentals)
    part2(weather_means, weather_errors)
    bin_centres, bin_means, bin_errors, slope, intercept = part3(temperature, rentals)
    part4(temperature, rentals)
    part5(year, weather, temperature, rentals)
    #plot needs results from parts 1 and 3, so pass them as arguments
    part6(temperature, rentals, weather_means, weather_errors, weather_days,
              bin_centres, bin_means, bin_errors, slope, intercept)

#ensures that the main() function is only called when the script is run directly, not when it is imported as a module in another script
if __name__ == "__main__":
    main()
