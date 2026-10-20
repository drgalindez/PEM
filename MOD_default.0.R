# Set up: Install Packages

#install.packages("neonUtilities")
#install.packages("neonOS")
#install.packages("terra")

# Set up: Load packages

library(terra)
library(plotly)
library(dplyr)
library(ggplot2)


# Get working directory
getwd()
# Set working directory to the folder where you want to save the data
setwd("C:/Users/drgal/Desktop/BU/EE-529-MOD&MON/EE529-PEM-Assignment/09-PEM-Assignment/R")

evergreen <- read.csv("C:/Users/drgal/Desktop/BU/EE-529-MOD&MON/EE529-PEM-Assignment/09-PEM-Assignment/output/site_02_evergreen_broadleaf_forest_daily.csv",
         header = TRUE, sep = ",", stringsAsFactors = FALSE)
cropland <- read.csv("C:/Users/drgal/Desktop/BU/EE-529-MOD&MON/EE529-PEM-Assignment/09-PEM-Assignment/output/site_11_cropland_daily.csv",
                      header = TRUE, sep = ",", stringsAsFactors = FALSE)
shrubland <- read.csv("C:/Users/drgal/Desktop/BU/EE-529-MOD&MON/EE529-PEM-Assignment/09-PEM-Assignment/output/site_09_open_shrubland_daily.csv",
                      header = TRUE, sep = ",", stringsAsFactors = FALSE)




# evergreen <- site_02_evergreen_broadleaf_forest_daily
View(evergreen)

mean_vpd <- mean(evergreen$vpd_Pa)
mean_vpd

summary(evergreen$vpd_Pa)

summary(evergreen$day_of_year)



  # Create a new column in the evergreen data frame to store the month names
evergreen$month [evergreen$day_of_year>=1 & evergreen$day_of_year<32] = 1
evergreen$month [evergreen$day_of_year>=32 & evergreen$day_of_year<60] = 2
evergreen$month [evergreen$day_of_year>=60 & evergreen$day_of_year<91] = 3
evergreen$month [evergreen$day_of_year>=91 & evergreen$day_of_year<121] = 4
evergreen$month [evergreen$day_of_year>=121 & evergreen$day_of_year<152] = 5
evergreen$month [evergreen$day_of_year>=152 & evergreen$day_of_year<182] = 6
evergreen$month [evergreen$day_of_year>=182 & evergreen$day_of_year<213] = 7
evergreen$month [evergreen$day_of_year>=213 & evergreen$day_of_year<244] = 8
evergreen$month [evergreen$day_of_year>=244 & evergreen$day_of_year<274] = 9
evergreen$month [evergreen$day_of_year>=274 & evergreen$day_of_year<305] = 10
evergreen$month [evergreen$day_of_year>=305 & evergreen$day_of_year<335] = 11
evergreen$month [evergreen$day_of_year>=335 & evergreen$day_of_year<366] = 12



# Create a new column in the cropland data frame to store the month names
cropland$month [cropland$day_of_year>=1 & cropland$day_of_year<32] = 1
cropland$month [cropland$day_of_year>=32 & cropland$day_of_year<60] = 2
cropland$month [cropland$day_of_year>=60 & cropland$day_of_year<91] = 3
cropland$month [cropland$day_of_year>=91 & cropland$day_of_year<121] = 4
cropland$month [cropland$day_of_year>=121 & cropland$day_of_year<152] = 5
cropland$month [cropland$day_of_year>=152 & cropland$day_of_year<182] = 6
cropland$month [cropland$day_of_year>=182 & cropland$day_of_year<213] = 7
cropland$month [cropland$day_of_year>=213 & cropland$day_of_year<244] = 8
cropland$month [cropland$day_of_year>=244 & cropland$day_of_year<274] = 9
cropland$month [cropland$day_of_year>=274 & cropland$day_of_year<305] = 10
cropland$month [cropland$day_of_year>=305 & cropland$day_of_year<335] = 11
cropland$month [cropland$day_of_year>=335 & cropland$day_of_year<366] = 12



# Create a new column in the shrubland data frame to store the month names
shrubland$month [shrubland$day_of_year>=1 & shrubland$day_of_year<32] = 1
shrubland$month [shrubland$day_of_year>=32 & shrubland$day_of_year<60] = 2
shrubland$month [shrubland$day_of_year>=60 & shrubland$day_of_year<91] = 3
shrubland$month [shrubland$day_of_year>=91 & shrubland$day_of_year<121] = 4
shrubland$month [shrubland$day_of_year>=121 & shrubland$day_of_year<152] = 5
shrubland$month [shrubland$day_of_year>=152 & shrubland$day_of_year<182] = 6
shrubland$month [shrubland$day_of_year>=182 & shrubland$day_of_year<213] = 7
shrubland$month [shrubland$day_of_year>=213 & shrubland$day_of_year<244] = 8
shrubland$month [shrubland$day_of_year>=244 & shrubland$day_of_year<274] = 9
shrubland$month [shrubland$day_of_year>=274 & shrubland$day_of_year<305] = 10
shrubland$month [shrubland$day_of_year>=305 & shrubland$day_of_year<335] = 11
shrubland$month [shrubland$day_of_year>=335 & shrubland$day_of_year<366] = 12




# Create a new column in the evergreen data frame to store the avgNPP for each month
evergreen$monthavgNPP [evergreen$day_of_year>=1 & evergreen$day_of_year<32] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=1 & evergreen$day_of_year<32])
evergreen$monthavgNPP [evergreen$day_of_year>=32 & evergreen$day_of_year<60] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=32 & evergreen$day_of_year<60])
evergreen$monthavgNPP [evergreen$day_of_year>=60 & evergreen$day_of_year<91] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=60 & evergreen$day_of_year<91])
evergreen$monthavgNPP [evergreen$day_of_year>=91 & evergreen$day_of_year<121] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=91 & evergreen$day_of_year<121])
evergreen$monthavgNPP [evergreen$day_of_year>=121 & evergreen$day_of_year<152] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=121 & evergreen$day_of_year<152])
evergreen$monthavgNPP [evergreen$day_of_year>=152 & evergreen$day_of_year<182] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=152 & evergreen$day_of_year<182])
evergreen$monthavgNPP [evergreen$day_of_year>=182 & evergreen$day_of_year<213] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=182 & evergreen$day_of_year<213])
evergreen$monthavgNPP [evergreen$day_of_year>=213 & evergreen$day_of_year<244] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=213 & evergreen$day_of_year<244])
evergreen$monthavgNPP [evergreen$day_of_year>=244 & evergreen$day_of_year<274] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=244 & evergreen$day_of_year<274])
evergreen$monthavgNPP [evergreen$day_of_year>=274 & evergreen$day_of_year<305] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=274 & evergreen$day_of_year<305])
evergreen$monthavgNPP [evergreen$day_of_year>=305 & evergreen$day_of_year<335] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=305 & evergreen$day_of_year<335])
evergreen$monthavgNPP [evergreen$day_of_year>=335 & evergreen$day_of_year<366] = mean(evergreen$npp_kgC_m2_day[evergreen$day_of_year>=335 & evergreen$day_of_year<366])

# Create a new column in the cropland data frame to store the avgNPP for each month
cropland$monthavgNPP [cropland$day_of_year>=1 & cropland$day_of_year<32] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=1 & cropland$day_of_year<32])
cropland$monthavgNPP [cropland$day_of_year>=32 & cropland$day_of_year<60] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=32 & cropland$day_of_year<60])
cropland$monthavgNPP [cropland$day_of_year>=60 & cropland$day_of_year<91] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=60 & cropland$day_of_year<91])
cropland$monthavgNPP [cropland$day_of_year>=91 & cropland$day_of_year<121] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=91 & cropland$day_of_year<121])
cropland$monthavgNPP [cropland$day_of_year>=121 & cropland$day_of_year<152] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=121 & cropland$day_of_year<152])
cropland$monthavgNPP [cropland$day_of_year>=152 & cropland$day_of_year<182] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=152 & cropland$day_of_year<182])
cropland$monthavgNPP [cropland$day_of_year>=182 & cropland$day_of_year<213] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=182 & cropland$day_of_year<213])
cropland$monthavgNPP [cropland$day_of_year>=213 & cropland$day_of_year<244] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=213 & cropland$day_of_year<244])
cropland$monthavgNPP [cropland$day_of_year>=244 & cropland$day_of_year<274] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=244 & cropland$day_of_year<274])
cropland$monthavgNPP [cropland$day_of_year>=274 & cropland$day_of_year<305] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=274 & cropland$day_of_year<305])
cropland$monthavgNPP [cropland$day_of_year>=305 & cropland$day_of_year<335] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=305 & cropland$day_of_year<335])
cropland$monthavgNPP [cropland$day_of_year>=335 & cropland$day_of_year<366] = mean(cropland$npp_kgC_m2_day[cropland$day_of_year>=335 & cropland$day_of_year<366])

# Create a new column in the shrubland data frame to store the avgNPP for each month
shrubland$monthavgNPP [shrubland$day_of_year>=1 & shrubland$day_of_year<32] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=1 & shrubland$day_of_year<32])
shrubland$monthavgNPP [shrubland$day_of_year>=32 & shrubland$day_of_year<60] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=32 & shrubland$day_of_year<60])
shrubland$monthavgNPP [shrubland$day_of_year>=60 & shrubland$day_of_year<91] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=60 & shrubland$day_of_year<91])
shrubland$monthavgNPP [shrubland$day_of_year>=91 & shrubland$day_of_year<121] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=91 & shrubland$day_of_year<121])
shrubland$monthavgNPP [shrubland$day_of_year>=121 & shrubland$day_of_year<152] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=121 & shrubland$day_of_year<152])
shrubland$monthavgNPP [shrubland$day_of_year>=152 & shrubland$day_of_year<182] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=152 & shrubland$day_of_year<182])
shrubland$monthavgNPP [shrubland$day_of_year>=182 & shrubland$day_of_year<213] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=182 & shrubland$day_of_year<213])
shrubland$monthavgNPP [shrubland$day_of_year>=213 & shrubland$day_of_year<244] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=213 & shrubland$day_of_year<244])
shrubland$monthavgNPP [shrubland$day_of_year>=244 & shrubland$day_of_year<274] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=244 & shrubland$day_of_year<274])
shrubland$monthavgNPP [shrubland$day_of_year>=274 & shrubland$day_of_year<305] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=274 & shrubland$day_of_year<305])
shrubland$monthavgNPP [shrubland$day_of_year>=305 & shrubland$day_of_year<335] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=305 & shrubland$day_of_year<335])
shrubland$monthavgNPP [shrubland$day_of_year>=335 & shrubland$day_of_year<366] = mean(shrubland$npp_kgC_m2_day[shrubland$day_of_year>=335 & shrubland$day_of_year<366])






 # Create a new data frame to store the mean NPP for each month
# monthly_table <- evergreen %>%
#   group_by(month) %>%
#   summarise(
#     vpd_Pa = mean(vpd_Pa, na.rm = TRUE)
#   )



  # Add a new column to the monthly_table data frame to store the month number
# monthly_table$num <- c(4,8,12,2,1,7,6,3,5,11,10,9)
  # Order the monthly_table data frame by the month number
# evergreen <- monthly_table[order(monthly_table$num),]

View(evergreen)
View(cropland)
View(shrubland)
View(monthly_table)

# Create a box plot of the mean VPD for each month using plotly
boxplot(vpd_Pa ~ month, data = evergreen, main = "Boxplot of VPD by Month", xlab = "Month", ylab = "VPD (Pa)")


# Create a Table for second variable/axis
monthly_temp1  <- aggregate(monthavgNPP  ~ month, evergreen, mean)
monthly_temp2 <- aggregate(monthavgNPP  ~ month, cropland, mean)
monthly_temp3 <- aggregate(monthavgNPP  ~ month, shrubland, mean)



# Merge all into one table
# monthly_temp <- merge(monthly_temp1, monthly_temp2, monthly_temp3, by = "month")
View(monthly_temp1)
View(monthly_temp2)
View(monthly_temp3)



# Create a boxplot for evergreen
ggplot(evergreen, aes(x = factor(month), y = vpd_Pa)) +
  geom_boxplot() +
  geom_line(data = monthly_temp1,
            aes(x = factor(month),
                y = monthavgNPP * 1000000),   # scale factor
            color = "red", linewidth = 0.75,
            group = 1) +
  scale_y_continuous(
    name = "VPD (Pa)",
    sec.axis = sec_axis(~ . / 100,
                        name = "NPP (mgC/m2/day)"))


# Create a boxplot for cropland
ggplot(cropland, aes(x = factor(month), y = vpd_Pa)) +
  geom_boxplot() +
  geom_line(data = monthly_temp2,
            aes(x = factor(month),
                y = monthavgNPP * 1000000),   # scale factor
            color = "red", linewidth = 0.75,
            group = 1) +
  scale_y_continuous(
    name = "VPD (Pa)",
    sec.axis = sec_axis(~ . / 100,
                        name = "NPP (mgC/m2/day)"))



# Create a boxplot for shrubland
ggplot(shrubland, aes(x = factor(month), y = vpd_Pa)) +
  geom_boxplot() +
  geom_line(data = monthly_temp3,
            aes(x = factor(month),
                y = monthavgNPP * 1000000),   # scale factor
            color = "red", linewidth = 0.75,
            group = 1) +
  scale_y_continuous(
    name = "VPD (Pa)",
    sec.axis = sec_axis(~ . / 100,
                        name = "NPP (mgC/m2/day)"))




#  Add a new column to store the mean VPD for each month
monthly_temp$vpd_Pa <- evergreen %>%
  group_by(month) %>%
  summarise(
    vpd_Pa = mean(vpd_Pa, na.rm = TRUE)
  )

# Create a bar plot of the mean VPD for each month using plotly
plot_ly(data = monthly_temp, x = ~month, y = ~vpd_Pa, type = 'bar', name = 'VPD') %>%
  layout(title = "Mean VPD by Month",
         xaxis = list(title = "Month"),
         yaxis = list(title = "Mean VPD (Pa)"))

