import {
    Button,
    chakra,
    FormControl,
    FormLabel,
    HTMLChakraProps,
    Input,
    Stack,
    Text,
    Link,
    useColorModeValue,
} from '@chakra-ui/react'
import { Link as RouterLink } from 'react-router-dom';
import * as React from 'react'

export const ForgetPasswordForm = (props: HTMLChakraProps<'form'>) => (
<chakra.form
    onSubmit={(e) => {
    e.preventDefault()
    // your login logic here
    }}
    {...props}
>
    <Stack spacing="6">
    <FormControl id="email">
        <FormLabel>Email address</FormLabel>
        <Input name="email" type="email" autoComplete="email" required />
    </FormControl>
    <Button type="submit" colorScheme="blue" size="lg" fontSize="md">
        Email me a reset link
    </Button>
    <Text mt="4" mb="8" align="center" maxW="md" fontWeight="medium">
        <Text as="span">Don't have an account? </Text>
        <Link
            color={useColorModeValue('blue.500', 'blue.200')}
            _hover={{ color: useColorModeValue('blue.600', 'blue.300') }}
            display={{ base: 'block', sm: 'inline' }}
            as={RouterLink}
            to="/signup">
                Sign up
        </Link>
    </Text>
    <Text mt="4" mb="8" align="center" maxW="md" fontWeight="medium">
        <Text as="span">Already have an account? </Text>
        <Link
            color={useColorModeValue('blue.500', 'blue.200')}
            _hover={{ color: useColorModeValue('blue.600', 'blue.300') }}
            display={{ base: 'block', sm: 'inline' }}
            as={RouterLink}
            to="/login">
                Log in
        </Link>
    </Text>
    </Stack>
</chakra.form>
)

